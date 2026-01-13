
try:
    from transformers import pipeline
    print("Import successful")
    p = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    print("Pipeline loaded")
    print(p("I love this!"))
except Exception as e:
    print(f"Error: {e}")
