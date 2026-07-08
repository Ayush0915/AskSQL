import os
import sys
from pathlib import Path

# Add project root to path before project imports
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import logging
from sqlalchemy import create_engine, text
from backend.app.config import config
from backend.app.rag.retriever import SchemaRetriever
from backend.app.llm.sql_generator import SQLGenerator
from backend.app.validator.sql_validator import SQLValidator


# Set up logging for evaluation
logging.basicConfig(level=logging.ERROR)  # Suppress info logs during eval
logger = logging.getLogger("asksql-eval")

eval_dir = Path(__file__).resolve().parent
questions_path = eval_dir / "eval_questions.json"

class EvalRunner:
    def __init__(self):
        # Use postgres admin user to execute both ground truth and generated query
        self.engine = create_engine(config.DATABASE_ADMIN_URL)
        self.retriever = SchemaRetriever()
        self.generator = SQLGenerator()
        self.validator = SQLValidator()

    def run_query(self, sql: str) -> list[tuple]:
        """
        Executes a SQL query and returns rows as a list of value tuples, 
        sorted by the values to make comparison order-independent where sorting is not enforced.
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            if not result.returns_rows:
                return []
            rows = result.fetchall()
            # Convert row objects (which are sequences) to tuples of raw values
            # Round floats to 2 decimal places to avoid precision mismatch
            cleaned_rows = []
            for r in rows:
                cleaned_row = []
                for val in r:
                    if isinstance(val, float):
                        cleaned_row.append(round(val, 2))
                    elif isinstance(val, (int, str)) or val is None:
                        cleaned_row.append(val)
                    else:
                        cleaned_row.append(str(val))
                cleaned_rows.append(tuple(cleaned_row))
            return cleaned_rows

    def compare_results(self, res_gen: list[tuple], res_gt: list[tuple]) -> bool:
        """
        Compares if the result sets are matching.
        """
        if len(res_gen) != len(res_gt):
            return False
            
        # Sort both result sets to be order-independent
        try:
            sorted_gen = sorted(res_gen, key=lambda x: str(x))
            sorted_gt = sorted(res_gt, key=lambda x: str(x))
            return sorted_gen == sorted_gt
        except Exception:
            return res_gen == res_gt

    def run_evaluation(self):
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
            
        total_questions = len(questions)
        passed = 0
        results_log = []
        
        print("\n" + "="*80)
        print(f"STARTING ASKSQL BENCHMARK EVALUATION ({total_questions} questions)")
        print("="*80 + "\n")
        
        difficulty_stats = {}
        
        for q in questions:
            q_id = q["id"]
            question = q["question"]
            gt_sql = q["ground_truth_sql"]
            diff = q["difficulty"]
            
            if diff not in difficulty_stats:
                difficulty_stats[diff] = {"total": 0, "passed": 0}
            difficulty_stats[diff]["total"] += 1
            
            print(f"[{q_id}/{total_questions}] [{diff.upper()}] Q: {question}")
            
            # Step 1: Retrieve schema context
            try:
                schema_context = self.retriever.retrieve_relevant_schemas(question, top_k=4)
            except Exception as e:
                print(f"  [ERROR] Retrieval Error: {e}")
                results_log.append({"id": q_id, "status": "FAIL", "reason": f"Retrieval Error: {e}"})
                continue
                
            # Step 2: Generate SQL
            try:
                gen_sql = self.generator.generate_sql(question, schema_context)
            except Exception as e:
                print(f"  [ERROR] Generation Error: {e}")
                results_log.append({"id": q_id, "status": "FAIL", "reason": f"Generation Error: {e}"})
                continue
                
            # Step 3: Validate SQL
            is_valid, reason = self.validator.validate_sql(gen_sql)
            if not is_valid:
                print(f"  [ERROR] Validation Failed: {reason}")
                print(f"     Generated SQL: {gen_sql}")
                results_log.append({"id": q_id, "status": "FAIL", "reason": f"Validation Error: {reason}", "generated_sql": gen_sql})
                continue
                
            # Step 4: Run queries and compare results
            try:
                # Add limits to avoid large outputs during testing
                sql_to_run = self.validator.enforce_limit(gen_sql, default_limit=100)
                gt_sql_to_run = self.validator.enforce_limit(gt_sql, default_limit=100)
                
                res_gen = self.run_query(sql_to_run)
                res_gt = self.run_query(gt_sql_to_run)
                
                is_correct = self.compare_results(res_gen, res_gt)
                if is_correct:
                    print("  [PASS]")
                    passed += 1
                    difficulty_stats[diff]["passed"] += 1
                    results_log.append({"id": q_id, "status": "PASS", "generated_sql": gen_sql})
                else:
                    print("  [FAIL] (Result set mismatch)")
                    print(f"     Ground Truth SQL: {gt_sql_to_run}")
                    print(f"     Generated SQL:    {sql_to_run}")
                    print(f"     GT rows: {len(res_gt)}, Gen rows: {len(res_gen)}")
                    if len(res_gt) > 0 and len(res_gen) > 0:
                        print(f"     Sample GT Row:  {res_gt[0]}")
                        print(f"     Sample Gen Row: {res_gen[0]}")
                    results_log.append({
                        "id": q_id, 
                        "status": "FAIL", 
                        "reason": "Result mismatch", 
                        "generated_sql": gen_sql,
                        "ground_truth_sql": gt_sql
                    })
            except Exception as e:
                print(f"  [ERROR] Execution Error: {e}")
                print(f"     Generated SQL: {gen_sql}")
                results_log.append({"id": q_id, "status": "FAIL", "reason": f"Execution Error: {e}", "generated_sql": gen_sql})

                
            print("-" * 50)
            
        accuracy = (passed / total_questions) * 100
        print("\n" + "="*80)
        print(f"EVALUATION SUMMARY")
        print(f"Overall Execution Accuracy: {accuracy:.2f}% ({passed}/{total_questions})")
        print("="*80)
        
        for diff, stats in difficulty_stats.items():
            diff_acc = (stats["passed"] / stats["total"]) * 100
            print(f"  - {diff.capitalize()}: {diff_acc:.2f}% ({stats['passed']}/{stats['total']})")
        print("="*80 + "\n")
        
        # Write results log file
        log_path = eval_dir / "eval_results.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({
                "accuracy": accuracy,
                "passed": passed,
                "total": total_questions,
                "detailed_results": results_log
            }, f, indent=2)

if __name__ == "__main__":
    # Add project root to path
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    runner = EvalRunner()
    runner.run_evaluation()
