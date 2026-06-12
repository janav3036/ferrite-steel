import json
from ferite_steel.ai import together_client

TOGETHER_MODEL = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'

def judge_quiz_answer(question_text, correct_answer, user_answer):
    system_prompt = (
        "You are a quiz evaluator for a steel distribution company's employee training system. "
        "You are given a question, the correct answer written by an admin, and the user's answer. "
        "Decide whether the user's answer is correct — allow for paraphrasing and different wording. "
        "Respond ONLY with a JSON object in this exact format: "
        "{\"correct\": true, \"explanation\": \"...\"} "
        "Keep the explanation under 3 sentences. "
        "If correct, briefly confirm why. If wrong, explain what the correct answer is."
    )
    user_message = (
        f"Question: {question_text}\n\n"
        f"Correct answer: {correct_answer}\n\n"
        f"User's answer: {user_answer}"
    )
    response = together_client.chat.completions.create(
        model=TOGETHER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=300,
        temperature=0.1,
    )
    raw = response.choices[0].message.content.strip()
    try:
        result = json.loads(raw)
        return {
            "correct": bool(result.get("correct")),
            "explanation": result.get("explanation", ""),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"correct": False, "explanation": raw}
    
def answer_question(question, chunks, cases):
    context_parts = []
    if chunks:
        context_parts.append("=== KNOWLEDGE BASE ===")
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[{i}] {chunk.chunk_text}")
    if cases:
        context_parts.append("=== CASE RECORDS ===")
        for case in cases:
            context_parts.append(
                f"Case: {case.title}\n"
                f"Problem: {case.problem_description}\n"
                f"Resolution: {case.resolution}"
            )
    context = '\n\n'.join(context_parts)
    system = (
        "You are a knowledgeable assistant for Ferrite Steel, an iron and steel distributor. "
        "Answer the user's question using only the provided context. "
        "If the answer is not in the context, say so — do not guess. "
        "Be concise and practical."
    )
    response = together_client.chat.completions.create(
        model=TOGETHER_MODEL,
        messages=[
            {"role": "system", "content": f"{system}\n\nContext:\n{context}"},
            {"role": "user", "content": question},
        ],
        max_tokens=512,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
