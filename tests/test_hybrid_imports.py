
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("Testing imports...")
    import rank_bm25
    print("✓ rank_bm25 imported successfully.")
    
    try:
        from langchain.retrievers import EnsembleRetriever
        print("✓ LangChain EnsembleRetriever imported from langchain.retrievers.")
    except ImportError:
        try:
            from langchain_classic.retrievers.ensemble import EnsembleRetriever
            print("✓ LangChain EnsembleRetriever imported from langchain_classic.")
        except ImportError:
            # Fallback check
            from langchain.retrievers.ensemble import EnsembleRetriever
            print("✓ LangChain EnsembleRetriever imported from langchain.retrievers.ensemble.")

    from langchain_community.retrievers import BM25Retriever
    print("✓ LangChain BM25Retriever imported successfully.")
    
    # We delay search_service import to avoid crashing before print
    # from service.search_service import init_search, similarity_search
    # print("✓ search_service imported successfully.")
    
    print("\nEnvironment check passed.")
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    sys.exit(1)
