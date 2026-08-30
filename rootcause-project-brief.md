# RootCause

**An AI misconception-diagnosis tool for teachers, built for the Prometheus August AI Challenge**

> RootCause reads a stack of open-ended student answers and figures out not just who got it wrong, but *why* — clustering shared misconceptions across a whole class and handing the teacher a targeted reteach plan in seconds.

| | |
|---|---|
| **Hackathon** | Prometheus August AI Challenge (Devpost) |
The Prometheus August AI Challenge: $1,500 in prizes! Join the next generation of AI and Machine Learning innovators
About the challenge
Welcome to the August AI Challenge, a premier virtual hackathon designed for the next generation of innovators, developers, and creators. This month, we are pushing the boundaries of artificial intelligence to solve real-world problems. Whether you are an AI enthusiast, a seasoned data scientist, or a creative designer, this challenge is a great opportunity to build, collaborate, and showcase your skills on a global stage.
Requirements
What to Build
Build an educational tool that leverages the power of AI/Machine Learning to transform how people learn, teach, or absorb information. Your project should aim to make knowledge more accessible, engaging, or personalized.
Originality: All code must be written during the hackathon window (August 17th – 29h). Using open-source libraries and pre-trained AI models is encouraged, but core application logic must be new.
What to Submit
A 2 minute demo video showcasing your project, as well as your Source Code (GitHub Repository, etc)!
Judging Criteria
Educational Impact (25 pts)
How effectively does the tool solve a real problem in education? Does it genuinely help people learn, teach, or understand a concept better?
Creative Use of AI/ML (25 Points)
How clever and meaningful is the integration of machine learning? We are looking for projects where AI is core to the functionality, not just an afterthought.
Technical Execution (25 Points)
Is the application functional, stable, and intuitive to use? Judges will look at the quality of the codebase, user interface (UI), and overall user experience (UX).
The Pitch & Demo (25 Points)
How well did the team communicate their vision? Points are awarded for a clear, concise, and engaging 2-minute video that clearly explains the "why" and "how" behind the project.
| **Core idea** | Cluster a class's open-ended answers into shared misconceptions, surfaced as a teacher dashboard |
| **Primary stack** | OpenRouter (`z-ai/glm-5.2:free`, then `nvidia/nemotron-3-ultra-550b-a55b:free`) + sentence-transformers + scikit-learn / HDBSCAN + React or Streamlit |

## Table of contents

1. [The problem](#1-the-problem)
2. [The idea](#2-the-idea)
3. [Why this wins the rubric](#3-why-this-wins-the-rubric)
4. [How it works — architecture](#4-how-it-works--architecture)
5. [Prompts and data schema](#5-prompts-and-data-schema)
6. [Tech stack](#6-tech-stack)
7. [MVP scope](#7-mvp-scope)
8. [Suggested repo structure](#8-suggested-repo-structure)
9. [Demo dataset](#9-demo-dataset)
10. [6-day build plan](#10-6-day-build-plan)
11. [Demo video script](#11-demo-video-script)
12. [Risks and mitigations](#12-risks-and-mitigations)
13. [Roadmap — what's next](#13-roadmap--whats-next)
14. [Sources](#14-sources)

---

## 1. The problem

Grading eats a huge share of a teacher's week, and almost none of that time goes toward actually understanding *why* a student got something wrong. US teachers report spending close to ten hours a week grading, nearly two-thirds call it one of the worst parts of the job, and the large majority take that work home with them [1]. Three in four say they'd hand it to an AI tool if it genuinely cut the load [1].

But speed isn't the real bottleneck — depth is. One workload analysis found that giving every student genuinely individualized feedback, on top of baseline grading, would take a teacher dozens of additional hours on top of an already full week [2]. That's exactly why it mostly doesn't happen, even though it's one of the highest-leverage things a teacher can do: in Hattie's meta-analysis of what actually moves student achievement, feedback lands around an effect size of 0.7 [3], comfortably above the 0.4 "hinge point" used to separate interventions worth prioritizing from the rest [4]. A more recent, independently run replication across more than 61,000 students still found a solid 0.48 [5].

So the gap isn't "teachers need to grade faster." It's "teachers have no scalable way to see what their class, as a group, actually believes — and no time to build one by hand." That's the specific, well-evidenced gap RootCause automates.

## 2. The idea

A teacher pastes or uploads a batch of open-ended answers to one question. Instead of marking each one right or wrong, RootCause:

1. Reads the reasoning underneath each answer, not just the answer itself.
2. Groups students who share the same underlying (often wrong) mental model.
3. Names each shared misconception in plain language.
4. Suggests one concrete reteach activity per misconception.
5. Optionally drafts a personalized note per student addressing *their* specific gap, instead of a generic "incorrect, try again."

**What it is not:** a tutor, a grading-speed tool, or a summative-assessment platform. It doesn't replace the teacher's judgment — it gives them, in seconds, a diagnostic view they currently can't get at all without reading every answer by hand and holding the patterns in their head.

**How it differs from existing AI grading tools** (EssayGrader, GRADED+, and similar): those tools make *one student's* feedback loop faster. RootCause answers a question those tools don't even ask — what does the *whole class, together*, actually believe, and where does it diverge from the truth? That's diagnosis, not grading. It's a genuinely different pipeline, not a faster version of the same one.

**Walkthrough example:** Ms. Alvarez gives her 8th-grade class a one-line exit-ticket question: *"Why does ice float on water?"* Thirty answers come back. She pastes them into RootCause. Thirty seconds later, a dashboard shows her that half the class thinks it's about weight ("ice is heavy, but it's cold, so it floats"), a fifth thinks ice traps air like a balloon, a fifth has no working model at all, and only three students are reasoning about density correctly. She now knows exactly what to reteach tomorrow morning, and to whom — something a stack of graded quizzes alone would never have told her.

## 3. Why this wins the rubric

| Criterion | Points | Why RootCause wins | Pitch one-liner |
|---|---|---|---|
| **Educational impact** | 25 | Targets a problem backed by decades of learning-science evidence (feedback is one of the highest-leverage moves in education research), and it scales — fix one teacher's blind spot and you improve the year for 30 students, not one. Note the rubric explicitly says "learn, **teach**, or understand" — most entrants default to student-facing tutors and leave the teacher-facing angle wide open. | "We didn't build another tutor. We built the thing that tells a teacher what to teach next." |
| **Creative use of AI/ML** | 25 | Not one prompt — a real pipeline: embeddings to cluster the reasoning, an LLM to label what each cluster means and draft the reteach suggestion. That hybrid of classical ML clustering and generative reasoning is a stronger "AI is core to the functionality" story than a chatbot wrapper. | "It's not a chatbot. It's a diagnostic pipeline — embeddings plus reasoning, not just a prompt." |
| **Technical execution** | 25 | Every component is well-trodden and low-risk: sentence embeddings, k-means or HDBSCAN, one dashboard screen. Nothing exotic to break mid-demo. | "Simple, stable pieces, combined in a way nobody else in the room will have built." |
| **Pitch & demo** | 25 | Built-in "wow" moment: a pile of raw, messy answers resolves into three labeled, counted clusters in under ten seconds on screen — an easy thing to make land in two minutes. | "Watch thirty confused answers turn into three clear insights in real time." |

## 4. How it works — architecture

```
Student responses (paste or upload)
            |
            v
 [1] LLM: extract reasoning  -->  one "mental model" summary per student
            |
            v
 [2] Embed each reasoning summary   (sentence-transformers, local, free)
            |
            v
 [3] Cluster the embeddings   (k-means, or HDBSCAN for auto-sized clusters)
            |
            v
 [4] LLM: label each cluster + draft a reteach suggestion
            |
            v
 [5] Dashboard UI  -->  teacher sees clusters, sizes, examples, suggestions
```

**Stage 1 — Reasoning extraction.** For each response, an LLM call extracts the underlying logic, not a correctness judgment. This is the step that makes the rest possible: two students can both say "it floats because it's cold" and both be wrong for the same reason, even if their sentences look nothing alike on the surface.

**Stage 2 — Embedding.** Turn each reasoning summary into a vector using a small local model (`all-MiniLM-L6-v2` via `sentence-transformers`). No API key, runs in milliseconds per response, good enough for classroom-sized batches.

**Stage 3 — Clustering.** Group the vectors. `HDBSCAN` is the better choice over plain k-means here: it doesn't require guessing the number of clusters up front, and it naturally buckets genuine outliers as "noise" — which maps perfectly onto the "no causal model yet" group instead of forcing a stray answer into a cluster it doesn't belong in.

**Stage 4 — Labeling and suggestions.** For each cluster, feed the LLM a handful of representative reasoning summaries and ask it to name the shared misconception, explain the gap versus the correct concept, and suggest one concrete reteach activity.

**Stage 5 — Dashboard.** Render the result as the mockup shown earlier in this conversation: summary stats up top, one card per cluster below with its size, an example response, and the suggested reteach.

## 5. Prompts and data schema

### Stage 1 prompt — reasoning extraction (per student)

```
System: You are analyzing a student's answer to identify the reasoning
behind it, not to judge whether it's correct.

User:
Question: {question_text}
Student answer: {student_answer}

In one or two sentences, describe the mental model or reasoning the
student is using to arrive at this answer — even if the answer happens
to be correct. Do not evaluate correctness. Focus only on the underlying
logic.

Respond as JSON: {"reasoning_summary": "..."}
```

### Stage 4 prompt — cluster labeling + reteach suggestion (per cluster)

```
System: You are an experienced teacher analyzing a group of students
who reasoned about a concept in a similar way.

User:
Question: {question_text}
Correct concept: {correct_concept}

Here are {n} students' reasoning summaries, grouped together because
they are semantically similar:
{list_of_reasoning_summaries}

1. Name this shared mental model in plain, teacher-friendly language
   (5-8 words).
2. In one sentence, explain the gap between this reasoning and the
   correct concept.
3. Suggest one concrete, concise reteach activity (1-2 sentences) that
   directly addresses this specific misconception.

Respond as JSON:
{"label": "...", "gap": "...", "reteach_suggestion": "..."}
```

### Optional — personalized feedback prompt (per student)

```
User:
Student answer: {student_answer}
Identified misconception: {cluster_label}
Correct concept: {correct_concept}

Write short (2-3 sentence), encouraging feedback directly to the
student. Acknowledge what's reasonable in their thinking, name the
specific gap without being discouraging, and point them toward the
correct idea. Do not simply say "incorrect."
```

### Data schema as it flows through the pipeline

```json
// After stage 1
{
  "student_id": "s01",
  "response_text": "Ice is heavy, but it's cold so it floats.",
  "reasoning_summary": "Believes weight and temperature determine floating, not density."
}

// After stage 3 (clustering)
{
  "cluster_id": 0,
  "student_ids": ["s01", "s04", "s07"],
  "size": 15
}

// After stage 4 (labeling)
{
  "cluster_id": 0,
  "label": "Mass, not density",
  "size": 15,
  "percentage": 50,
  "example_response": "Ice is heavy, but it's cold so it floats.",
  "reteach_suggestion": "Compare equal-mass blocks of wood and steel in water."
}
```

## 6. Tech stack

| Layer | Tool | Why |
|---|---|---|
| LLM calls | OpenRouter (GLM, then Nemotron fallback) | Reasoning extraction and cluster labeling, with three GLM attempts before the free fallback |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Free, local, no extra API key, fast enough for a classroom-sized batch |
| Clustering | `scikit-learn` (KMeans) or `hdbscan` | HDBSCAN auto-picks cluster count and handles outliers as "unclear" |
| Backend | FastAPI (Python) | Pairs naturally with the ML pieces above |
| Frontend | Next.js / React + Tailwind, or Streamlit | Streamlit = fastest path to something working; React = more UI polish |
| Deploy | Vercel + Render/Railway, or Streamlit Community Cloud | Judges need a public link they can click, not just a video |

## 7. MVP scope

**Must-have — the demo doesn't work without these:**

- [ ] Paste or upload a batch of open-ended answers to one question
- [ ] LLM extracts the reasoning behind each answer, not just correct/incorrect
- [ ] Embed and cluster those reasoning summaries into groups
- [ ] LLM names each cluster in plain language and drafts one reteach suggestion
- [ ] Dashboard screen showing clusters, counts, examples, and suggestions

**Nice-to-have — add in this order if time remains:**

- [ ] Auto-drafted personalized feedback per student
- [ ] A small seed library of documented misconceptions for one subject (instant credibility — "this matches a known, research-documented misconception" lands very well with judges)
- [ ] Photo or handwriting upload via OCR
- [ ] A mocked-up (non-functional) teaser screen for a live, in-lecture version, to show the roadmap without over-promising what ships this week

## 8. Suggested repo structure

```
rootcause/
  backend/
    main.py                 # FastAPI app
    pipeline/
      extract.py             # stage 1 — reasoning extraction
      embed.py                # stage 2 — embeddings
      cluster.py              # stage 3 — clustering
      label.py                 # stage 4 — labeling + suggestions
    requirements.txt
  frontend/
    ...                       # Next.js / React app, or streamlit_app.py
  demo_data/
    synthetic_responses.json  # see section 9
  README.md
```

## 9. Demo dataset

Fifteen synthetic, hand-written example responses to seed and test the pipeline — six in the majority misconception, three each in the other two, and three showing correct reasoning. Ask an LLM to generate more variations from this seed to reach a full class size of around 30 for the actual demo recording.

| Cluster | Count in sample | Share |
|---|---|---|
| Mass, not density | 6 | 40% |
| Trapped air, like a balloon | 3 | 20% |
| No causal model yet | 3 | 20% |
| Applies density correctly | 3 | 20% |

```json
[
  {"student_id": "s01", "response": "Ice is heavy, but it's cold so it floats.", "expected_cluster": "mass_not_density"},
  {"student_id": "s02", "response": "It must be lighter than the water around it because it's frozen.", "expected_cluster": "mass_not_density"},
  {"student_id": "s03", "response": "It floats because it's solid, and solids are lighter than liquids.", "expected_cluster": "mass_not_density"},
  {"student_id": "s04", "response": "The ice pushes down but the water pushes back harder since the ice is smaller.", "expected_cluster": "mass_not_density"},
  {"student_id": "s05", "response": "Cold things float because heat sinks and cold rises.", "expected_cluster": "mass_not_density"},
  {"student_id": "s06", "response": "Ice weighs less than the same size chunk of water, so it stays up.", "expected_cluster": "mass_not_density"},
  {"student_id": "s07", "response": "There's air inside the ice, so it floats like a balloon.", "expected_cluster": "trapped_air"},
  {"student_id": "s08", "response": "When water freezes it traps air bubbles, and that makes it float.", "expected_cluster": "trapped_air"},
  {"student_id": "s09", "response": "Ice has tiny holes full of air that keep it up, like foam.", "expected_cluster": "trapped_air"},
  {"student_id": "s10", "response": "Not sure - it just floats, I've always seen it happen.", "expected_cluster": "no_causal_model"},
  {"student_id": "s11", "response": "I think it's about temperature but I don't know exactly how.", "expected_cluster": "no_causal_model"},
  {"student_id": "s12", "response": "Because it's ice and ice floats on water, that's just how it works.", "expected_cluster": "no_causal_model"},
  {"student_id": "s13", "response": "Ice is less dense than liquid water, so it displaces enough water to float.", "expected_cluster": "correct"},
  {"student_id": "s14", "response": "Water expands when it freezes, so the same mass takes up more space, making ice less dense than liquid water.", "expected_cluster": "correct"},
  {"student_id": "s15", "response": "Floating depends on density, not weight, and ice is less dense than the water it's floating in.", "expected_cluster": "correct"}
]
```

## 10. 6-day build plan

### Day 1 — Aug 23 (today): lock scope, set up, seed data
- [ ] Freeze the MVP feature list so scope can't creep
- [ ] Set up the repo and environments
- [ ] Generate a synthetic dataset of ~30 responses from the seed above

### Day 2 — Aug 24: build the core pipeline
- [ ] Wire up stages 1-3 (extract, embed, cluster) end to end
- [ ] Get it working ugly on the synthetic dataset before touching UI

### Day 3 — Aug 25: labeling and suggestions
- [ ] Add stage 4 (cluster labeling + reteach suggestions)
- [ ] If time allows, add personalized per-student feedback

### Day 4 — Aug 26: build the dashboard UI
- [ ] Build the screen shown in this brief: stats, cluster cards, examples, suggestions
- [ ] Keep it clean and uncluttered over feature-complete

### Day 5 — Aug 27: add credibility, then deploy
- [ ] Seed one subject with a small library of documented misconceptions
- [ ] Deploy with a public link (Vercel, Render, Railway, or Streamlit Cloud)

### Day 6 — Aug 28: rehearse and record
- [ ] Write and time the 2-minute script (see section 11)
- [ ] Record the paste-to-dashboard moment as one clean take

### Day 7 — Aug 29: final edit, submit early
- [ ] Edit the video down, clean up the README
- [ ] Submit well before the deadline — don't wait for the last hour

## 11. Demo video script

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:15 | Teacher's desk, a stack of ungraded papers | "Thirty kids just answered one question. Half of them got it wrong. The teacher has ten minutes before her next class to figure out why — for each of them." |
| 0:15–0:30 | Cut to the stat: hours spent grading | "Teachers spend close to ten hours a week grading — and almost none of it goes toward understanding *why* a student got something wrong. That's the gap RootCause closes." |
| 0:30–1:30 | Live demo: paste responses, dashboard appears | Paste in the 30 responses. Let the dashboard render. Walk through two clusters out loud, in plain English, like you're explaining a kid's thinking to their teacher. Read one reteach suggestion aloud. |
| 1:30–1:50 | Zoom out on the dashboard | "This catches confusion while there's still time to fix it — before it becomes a bad grade. And it works for any subject, any open-ended question, any class size." |
| 1:50–2:00 | Logo / name / link | Show the name and tagline. Close clean — no trailing filler. |

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Real student data raises privacy questions (FERPA/COPPA) | Build and demo entirely on synthetic data generated by an LLM. Sidesteps privacy completely and gives full control over how clean the clusters look on camera. |
| Clustering gets noisy with small sample sizes | Pick a demo question where misconceptions are genuinely well-documented and well-separated (density/buoyancy, photosynthesis, order of operations) rather than leaving cluster count to chance. |
| Live demo breaks on stage/on camera | Record the core demo moment in advance as a clean take, even if other parts of the video are live narration over screen capture. |
| Scope creep eats the whole week | Treat section 7's must-have list as a hard boundary until it's done — nice-to-haves only after the core loop works end to end. |

## 13. Roadmap — what's next

Worth one line in the pitch, even unbuilt — shows judges there's a vision beyond the week:

- **Live, in-lecture "pulse" mode** — students flag confusion in real time during a lecture; the tool correlates the timestamp against what the teacher was saying at that moment, not just a raw confusion count.
- **Multi-level reteach suggestions** — generate the reteach note at a few different scaffolding or reading levels, borrowing the same "adapt content to a specific need" logic that would power an accommodation/IEP-focused tool.
- **Semester-long tracking** — follow the same class's misconception patterns across a whole term, not just one question.
- **Deeper misconception taxonomy** — seed more subjects from established research bases (e.g. physics education's Force Concept Inventory) rather than one hand-built example.

## 14. Sources

1. Learnosity / Perspectus Global survey, via Business Wire — grading hours, workload sentiment: https://www.businesswire.com/news/home/20250326730498/en/A-Third-of-US-Teachers-Considered-Leaving-Education-Due-to-Grading-Workload-Says-New-Research-by-Learnosity
2. Solved Consulting — cost of personalized feedback at scale: https://www.solvedconsulting.com/blog/how-much-time-do-middle-and-high-school-teachers-spend-grading-student-work
3. Wikipedia, "Visible learning" — Hattie's effect-size ranking (feedback ≈ 0.73): https://en.wikipedia.org/wiki/Visible_learning
4. Renaissance — explanation of Hattie's 0.40 "hinge point": https://www.renaissance.com/blog/the-john-hattie-effect-size-in-educational-research-what-is-it-and-how-is-it-used/
5. Frontiers in Psychology (2020), "The Power of Feedback Revisited" — independent replication, d = 0.48: https://doaj.org/article/d0708ec1b83041839fa99c22b4403c1d
6. Prometheus AI Challenge resources page — suggested tools and APIs: https://prometheus-july-ai-challenge.devpost.com/resources
7. Hackathon Radar — Prometheus AI Challenge team size and format: https://www.hackathonradar.com/database/hackathon/3be6030a-41d5-41b5-9220-0db10123b308
