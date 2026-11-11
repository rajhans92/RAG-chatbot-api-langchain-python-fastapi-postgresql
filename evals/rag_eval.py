import time, uuid, httpx
from dotenv import load_dotenv
from langsmith import evaluate
from openevals.llm import create_llm_as_judge
from openevals.prompts import (
    RAG_RETRIEVAL_RELEVANCE_PROMPT,
    RAG_GROUNDEDNESS_PROMPT,
    RAG_HELPFULNESS_PROMPT,
    CORRECTNESS_PROMPT,
)

JUDGE = "openai:gpt-4o-mini"   
load_dotenv()

DEBUG_URL = "http://127.0.0.1:8000/api/v1/chatbot/evaluation"

def rag_target(inputs: dict) -> dict:
    start = time.time()
    try:
        r = httpx.post(
            DEBUG_URL,
            json={
                "message": inputs["question"],
                "documentId": [1],
            },
            headers={"userId": "1", "sessionId": "1"},
            timeout=60, follow_redirects=True,
        )
        r.raise_for_status()
        d = r.json()
        return {"answer": d["answer"], "contexts": d["contexts"],
                "latency": time.time() - start, "error": None}
    except httpx.HTTPStatusError as e:
        err = f"{e.response.status_code}: {e.response.text[:300]}"
        print("==>", inputs["question"], err)
        return {"answer": "", "contexts": [], "sources": [],
                "latency": time.time() - start, "error": err}
    except Exception as e:
        return {"answer": "", "contexts": [],
                "latency": time.time() - start, "error": repr(e)}


# ---------- Retrieval layer ----------

_relevance = create_llm_as_judge(
    prompt=RAG_RETRIEVAL_RELEVANCE_PROMPT, feedback_key="context_relevance", model=JUDGE)

def context_relevance(inputs, outputs):
    return _relevance(inputs=inputs["question"],
                      context="\n\n".join(outputs["contexts"]))

# ---------- Generation layer ----------
_grounded = create_llm_as_judge(
    prompt=RAG_GROUNDEDNESS_PROMPT, feedback_key="faithfulness", model=JUDGE)

def faithfulness(outputs):
    return _grounded(outputs=outputs["answer"],
                     context="\n\n".join(outputs["contexts"]))

_helpful = create_llm_as_judge(
    prompt=RAG_HELPFULNESS_PROMPT, feedback_key="answer_relevance", model=JUDGE)

def answer_relevance(inputs, outputs):
    return _helpful(inputs=inputs["question"], outputs=outputs["answer"])

# ---------- End-to-end layer ----------
_correct = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT, feedback_key="correctness", model=JUDGE)

def correctness(inputs, outputs, reference_outputs):
    return _correct(inputs=inputs["question"], outputs=outputs["answer"],
                    reference_outputs=reference_outputs["expected"])

# ---------- Operational ----------
def no_error(outputs):
    return {"key": "no_error",
            "score": int(outputs.get("error") is None and bool(outputs.get("answer")))}

def latency_ok(outputs):
    return {"key": "latency_under_8s", "score": int(outputs.get("latency", 999) < 8)}

if __name__ == "__main__":
    evaluate(
        rag_target,
        data="rag-golden-v1",
        evaluators=[ context_relevance, faithfulness,
                    answer_relevance, correctness, no_error, latency_ok],
        experiment_prefix="rag-baseline",
        max_concurrency=2,
    )