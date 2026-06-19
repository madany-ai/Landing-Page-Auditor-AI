from duckduckgo_search import DDGS
with DDGS() as ddgs:
    print(list(ddgs.text("طقم حلل جرانيت", backend="lite", max_results=5)))
