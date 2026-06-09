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