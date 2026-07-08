import sys

def main():
    print("Notice: Static pre-embedding of schema descriptions is obsolete.")
    print("AskSQL now uses a dynamic, session-scoped upload flow using DuckDB.")
    print("Schema metadata is generated automatically during CSV upload and indexed in memory/disk.")
    sys.exit(0)

if __name__ == "__main__":
    main()
