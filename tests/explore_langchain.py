
try:
    import langchain
    print(f"LangChain Version: {langchain.__version__}")
    
    try:
        import langchain.retrievers
        print("langchain.retrievers imported.")
        print(dir(langchain.retrievers))
    except ImportError as e:
        print(f"Failed to import retrievers: {e}")
        
    try:
        from langchain.retrievers import EnsembleRetriever
        print("EnsembleRetriever imported directly.")
    except ImportError:
        print("EnsembleRetriever NOT found in langchain.retrievers")

except ImportError:
    print("LangChain not installed.")
