import os
import fire
import json
from pathlib import Path
from datasets import load_dataset
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from loguru import logger
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # base_url=os.getenv("OPENAI_BASE_URL"),
)

@dataclass
class EvalQA:
    repo_name: str = 'django'
    dataset_dir: str = 'eval/data/qa'
    eval_dir: str = 'eval_results/qa/django_e13b714/gpt41mini/v0'
    num_workers: int = 1

    def __post_init__(self):
        self.dataset_dir = Path(self.dataset_dir)
        self.eval_dir = Path(self.eval_dir)
        self.dataset = load_dataset('json', data_files=str(self.dataset_dir / f'{self.repo_name}.jsonl'), split='train')
        self.id_to_q = {s['instance_id']: s['problem_statement'].strip() for s in self.dataset}
        # load reference answers
        ref_dataset = load_dataset('json', data_files=str(self.dataset_dir / 'reference' / f'{self.repo_name}.jsonl'), split='train')
        self.q_to_ans = {s['question'].strip(): s['answer'].strip() for s in ref_dataset}
        logger.info(f'{len(self.q_to_ans) = }')
        self.id_to_ans = {id_: self.q_to_ans[q] for id_, q in self.id_to_q.items()}

    def score_answer(self, instance_id: str, question: str, reference: str, candidate: str, num_samples: int = 3) -> dict:
        # ... existing code ...
        prompt = f"""You are a professional evaluator. Please rate the candidate answer against the reference answer based on five criteria.
    Evaluation Criteria and Scoring Guidelines (each scored 1 to 10):
        1. Correctness:
            10 — Completely correct; core points and details are accurate with no ambiguity.
            8-9 — Mostly correct; only minor details are slightly inaccurate or loosely expressed.
            6-7 — Partially correct; some errors or omissions, but main points are generally accurate.
            4-5 — Several errors or ambiguities that affect understanding of the core information.
            2-3 — Many errors; misleading or fails to convey key information.
            1 — Serious errors; completely wrong or misleading.
        2. Completeness:
            10 — Covers all key points from the reference answer without omission.
            8-9 — Covers most key points; only minor non-critical information missing.
            6-7 — Missing several key points; content is somewhat incomplete.
            4-5 — Important information largely missing; content is one-sided.
            2-3 — Covers very little relevant information; seriously incomplete.
            1 — Covers almost no relevant information; completely incomplete.
        3. Relevance:
            10 — Content fully focused on the question topic; no irrelevant information.
            8-9 — Mostly focused; only minor irrelevant or peripheral information.
            6-7 — Generally on topic; some off-topic content but still relevant overall.
            4-5 — Topic not sufficiently focused; contains considerable off-topic content.
            2-3 — Content deviates from topic; includes excessive irrelevant information.
            1 — Majority of content irrelevant to the question.
        4. Clarity:
            10 — Fluent language; clear and precise expression; very easy to understand.
            8-9 — Mostly fluent; clear expression with minor unclear points.
            6-7 — Generally clear; some expressions slightly unclear or not concise.
            4-5 — Expression somewhat awkward; some ambiguity or lack of fluency.
            2-3 — Language obscure; sentences are not smooth; hinders understanding.
            1 — Expression confusing; very difficult to understand.
        5. Reasoning:
            10 — Reasoning is clear, logical, and well-structured; argumentation is excellent.
            8-9 — Reasoning is clear and logical; well-structured with solid argumentation.
            6-7 — Reasoning generally reasonable; mostly clear logic; minor jumps.
            4-5 — Reasoning is average; some logical jumps or organization issues.
            2-3 — Reasoning unclear; lacks logical order; difficult to follow.
            1 — No clear reasoning; logic is chaotic.

INPUT:
<question>
{question}
</question>

<reference_answer>
{reference}
</reference_answer>

<candidate_answer>
{candidate}
</candidate_answer>

OUTPUT:
    Please output ONLY a JSON object with 5 integer fields in the range [1,10], corresponding
    to the evaluation scores:
    {{
        "correctness": <1-10>,
        "completeness": <1-10>,
        "relevance": <1-10>,
        "clarity": <1-10>,
        "reasoning": <1-10>
    }}

REQUIREMENT:
    No explanation, no extra text, no formatting other than valid JSON"""
        score_json_path = self.eval_dir / 'scores' / f'{instance_id}.json'
        if score_json_path.is_file():
            with score_json_path.open() as f:
                return json.load(f)['scores_avg']
        score_json_path.parent.mkdir(parents=True, exist_ok=True)

        def parse_scores(score_str: str) -> dict:
            try:
                score_str = score_str.strip('```json').strip('```').strip()
                scores = json.loads(score_str)
                # Validate all dimensions are in range 0-10
                for key in ["correctness", "completeness", "clarity", "relevance", "reasoning"]:
                    if key not in scores or not (0 <= scores[key] <= 10):
                        logger.error(f"Score validation failed: {key} = {scores.get(key)}")
                        return {}
                return scores
            except Exception as e:
                logger.error(f"JSON parsing failed: {e}")
                return {}

        response = client.chat.completions.create(
            model='gpt-5.2',
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            # temperature=0.8,
            n=num_samples,
            reasoning_effort='low',
            max_completion_tokens=4096,
        )
        scores_list: list[dict] = []
        for choice in response.choices:
            score_str = choice.message.content.strip()
            scores = parse_scores(score_str)
            if scores:
                scores_list.append(scores)
        
        if not scores_list:
            return {}
        scores_avg = {k: sum(d[k] for d in scores_list) / len(scores_list) for k in scores_list[0]}
        with score_json_path.open('w') as f:
            json.dump({'scores_list': scores_list, 'scores_avg': scores_avg}, f, indent=2)
        logger.info(f'{scores_avg = } -> {score_json_path = }')
        return scores_avg
    
    def run(self) -> dict:
        with (self.eval_dir / 'preds.json').open() as f:
            preds = json.load(f)
        logger.info(f'{len(preds) = }')
        id_to_pred = {id_: s['model_patch'].strip() for id_, s in preds.items()}
        id_to_scores: dict[str, dict] = {}
        if self.num_workers <= 1:
            for id_, pred in tqdm(id_to_pred.items(), total=len(id_to_pred)):
                scores = self.score_answer(id_, self.id_to_q[id_], self.id_to_ans[id_], pred)
                if scores:
                    id_to_scores[id_] = scores
        else:
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = {
                    executor.submit(self.score_answer, id_, self.id_to_q[id_], self.id_to_ans[id_], pred): id_ 
                    for id_, pred in id_to_pred.items()
                }
                for future in tqdm(as_completed(futures), total=len(id_to_pred)):
                    id_ = futures[future]
                    scores = future.result()
                    if scores:
                        id_to_scores[id_] = scores
        
        scores_avg = {
            k: sum(d[k] for d in id_to_scores.values()) / len(id_to_scores)
            for k in list(id_to_scores.values())[0]
        }
        scores_avg['overall'] = sum(scores_avg.values()) / len(scores_avg)
        with (self.eval_dir / 'scores_avg.json').open('w') as f:
            json.dump(scores_avg, f, indent=2)
        return scores_avg


if __name__ == '__main__':
    fire.Fire(EvalQA)
