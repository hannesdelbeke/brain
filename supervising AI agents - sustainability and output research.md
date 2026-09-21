---
created: 2026-09-21
tags:
  - cognitive-science
  - ai-agents
  - productivity
  - human-factors
  - code-review
  - research
aliases:
  - is supervising AI sustainable
  - architect and review workflow with AI
  - human factors of AI delegation
  - supervisory control of coding agents
  - how to maximise long-term output with AI agents
  - automation complacency in AI-assisted work
---

> [!summary] eli5
> planning work and handing the execution to an AI is not a new kind of job. it is **supervisory control**, the same shape as an autopilot and a pilot, and aviation and medicine have measured what it does to the human for forty years. the reliable findings are that routine performance goes up, failure-case performance goes down, monitoring is tiring rather than restful, and the hands-on skill you are no longer using decays faster than physical skill does.
> on output the evidence splits by who you are: controlled trials show large gains for less experienced people on well-scoped tasks, and the one trial run on experienced maintainers working in their own codebase measured them **19% slower while they believed they were 20% faster**. the fatigue risk is not decision fatigue, which failed to replicate twice at scale, it is sustained evaluative attention, which does degrade and which this workflow produces all day.
> **needs from you:** one decision — whether to keep a share of work where you execute rather than review. the evidence supports doing so, because recent practice frequency predicts skill retention better than total career experience does, so the case for it is skill maintenance rather than output. a reasonable starting share is one task in five. there is no study that names the right number, so treat it as a bet rather than a finding.

> lets see if we can find research that applies or is close to what we do. we dont program. we architect. i talk to ai. define a plan. ai executes plan. i aim to keep high level. but i also have to review. i ask ai to review so i review high level but still lots of cognitive things. how sustainable is this. and how to maximise output long term? find research

**why:** [[cognitive limits on deep work and recovery science]]

The workflow of planning, delegating execution and reviewing the result is **supervisory control**, and it has a mature research literature attached to it from aviation, air traffic control, process plants and radiology. That literature is more relevant here than the deep-work literature, because the question is not how many hours of hard thinking a person can sustain but what happens to a person whose job has become monitoring an executor. The short version is that the costs are real, measured, and almost all of them land on the review step rather than the planning step. Output effects are genuinely mixed and depend heavily on experience level and task realism, so the sections below keep the negative and positive trials side by side rather than picking one.

Related: [[cognitive limits on deep work and recovery science]], [[code review]], [[cognitive load]], [[attention switching]], [[AI agent]], [[limited brain working memory]], [[Maker vs Manager Schedule]]

## What supervisory control does to the supervisor

**Bainbridge (1983)** named the problem in *Automatica* 19(6) 775-779 ([DOI](https://doi.org/10.1016/0005-1098(83)90046-8)): automating execution leaves the human with monitoring, which is the task humans are worst at, while the hands-on skill needed to intervene decays through disuse. This is an argued essay rather than an empirical study, but the empirical work since has largely borne it out.

**Onnasch, Wickens, Li & Manzey (2014)** meta-analysed degree-of-automation studies in *Human Factors* 56(3) 476-488 ([DOI](https://doi.org/10.1177/0018720813501549)) and found the pattern now called the **lumberjack effect**: raising the degree of automation improves routine performance and lowers workload, while degrading situation awareness and failure-mode performance. The higher you sit, the better the good days and the worse the bad ones.

**Endsley & Kiris (1995)** in *Human Factors* 37(2) 381-394 ([DOI](https://doi.org/10.1518/001872095779064555)) traced the mechanism to the shift from active generation to passive processing of someone else's solution, and found that intermediate levels of control — where the human retains consent or veto over each step — preserved situation awareness better than full automation did. Your instinct to stay high-level but keep review rights is the intermediate condition, and it is the condition that tested best.

**Parasuraman & Manzey (2010)** reviewed complacency and bias in *Human Factors* 52(3) 381-410 ([DOI](https://doi.org/10.1177/0018720810376055)). Two distinct failures matter here:

* **complacency** is attentional — checking the automation less often than the task warrants, and it gets worse as concurrent workload rises.
* **automation bias** is decisional — accepting a wrong output, or failing to act because no warning was raised.
* **expertise does not protect you.** Both effects appear in domain experts as well as novices, which rules out the obvious defence.
* **trust drives both**, and trust is calibrated against surface features. Confident, fluent, well-formatted output reads as reliable whether or not it is.

**Lee & See (2004)** in *Human Factors* 46(1) 50-80 ([DOI](https://doi.org/10.1518/hfes.46.1.50_30392)) separate trust **calibration** from trust **resolution** — you can be right on average about how reliable a system is and still be unable to tell which specific outputs are the bad ones. Resolution is the thing an LLM makes hardest, because output quality is uncorrelated with output polish.

**Dzindolet, Peterson, Pomranky, Pierce & Beck (2003)** ran the reliance experiments in *International Journal of Human-Computer Studies* 58(6) 697-718 ([DOI](https://doi.org/10.1016/S1071-5819(03)00038-7), N=180) and found two things worth holding together. The **first-failure effect**: watching an automated aid fail once collapses trust disproportionately. And the more awkward result for how agents are built today — **providing an explanation for the aid's errors raised trust and reliance even when the explanation did not justify the reliance**. Reasoning traces are persuasive independently of whether they are correct.

**Warm, Parasuraman & Matthews (2008)** established in *Human Factors* 50(3) 433-441 ([DOI](https://doi.org/10.1518/001872008X312152)) that vigilance is resource-consuming rather than restful — sustained monitoring produces measurable workload and stress, and the performance decrement appears within the first 15 to 30 minutes. Watching an agent work is not a break.

## Does delegating execution actually raise output

The controlled trials disagree with each other in a way that is informative rather than just noisy: the gains concentrate where tasks are well-scoped and participants are less experienced.

* **Peng, Kalliamvakou, Cihon & Demirer (2023)** ([arXiv:2302.06590](https://arxiv.org/abs/2302.06590), N=95 freelance programmers) measured a **55.8% speedup** with GitHub Copilot on a single HTTP-server task. Preprint, and several authors work at GitHub and Microsoft studying their own product.
* **Paradis et al. (2024)** ran an enterprise RCT at Google, peer-reviewed at ICSE SEIP 2025 ([arXiv:2410.12944](https://arxiv.org/abs/2410.12944), N=96 engineers), and found roughly **21% faster** on a complex C++ task, with a wide confidence interval. All authors and participants were Google employees evaluating Google's tools.
* **Cui, Demirer, Jaffe, Musolff, Peng & Salz (2026)** pooled three field experiments in *Management Science* ([DOI](https://doi.org/10.1287/mnsc.2025.00535), N=4,867 developers at Microsoft, Accenture and one Fortune 100 firm) and found a **26% increase in completed tasks**, with adoption and gains both concentrated among less experienced developers.
* **Becker, Rush, Barnes & Rein (2025)** ran the trial closest to your situation — experienced open-source maintainers, real tasks, repositories they averaged five years on ([arXiv:2507.09089](https://arxiv.org/abs/2507.09089), N=16, 246 tasks). They were **19% slower with AI, and estimated afterwards that they had been 20% faster**. A 39-point gap between measured and perceived effect. Small N and a preprint, so weight it accordingly, but the perception gap is the finding that transfers.

At the system rather than individual level, Google's **DORA** programme reports the same tension from survey data rather than experiment. The [2024 report](https://dora.dev/research/2024/dora-report/) found that as AI adoption rose 25%, delivery throughput fell an estimated 1.5% and delivery stability fell an estimated 7.2%, with the proposed mechanism being larger batch sizes arriving faster than the delivery pipeline can absorb. The [2025 report](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report) found throughput had reversed to positive while the negative relationship with stability persisted. These are industry surveys with a vendor interest, not controlled trials, so read the direction and not the decimals.

**The mechanism that reconciles the split** comes from **Lee, Sarkar, Tankelevitch, Drosos, Rintel, Banks & Wilson (2025)** at CHI 2025 ([Microsoft Research](https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/), N=319 knowledge workers, 936 reported episodes): generative AI shifts cognitive effort from information gathering toward **verification, integration and task stewardship**. The work is not removed, it changes type. They also found that higher confidence in the AI predicts less critical thinking while higher confidence in oneself predicts more — the two confidences pull in opposite directions. Self-reported survey data, so the causal direction is not established.

## Review is the bottleneck, and asking the AI to review does not move it

The widely repeated **200-400 lines per hour** review limit is not a peer-reviewed finding. It traces to a **vendor whitepaper from SmartBear and Cisco** (N=50 developers, 2,500 reviews, 3.2M lines over 10 months), which reported defect density falling below average in 87% of cases once reviewers exceeded roughly 450 lines per hour. The direction is consistent with peer-reviewed work but the specific numbers carry a commercial interest and should not be cited as research.

What is peer-reviewed is what reviewers actually do at scale. **Sadowski, Söderberg, Church, Sipko & Bacchelli (2018)** analysed nine million reviewed changes at Google for ICSE-SEIP ([DOI](https://doi.org/10.1145/3183519.3183525)) and found the median change is around **24 lines**, 90% of reviews touch under 10 files, and the working purpose of review has shifted from defect detection toward **correctness checking, comprehension and knowledge transfer**. **Rigby & Bird (2013)** at FSE ([DOI](https://doi.org/10.1145/2491411.2491444)) found convergent medians of 29 to 100 lines across AMD, Bing and Office, and that participating in review raises the number of distinct files a developer knows about by **66 to 150%**. Review is how you stay oriented in a system you are not writing, which matters more in your workflow than in a conventional one.

Two findings explain why reviewing agent output is harder than reviewing a colleague's. **Ebert, Castor, Novielli & Serebrenik (2021)** in *EMSE* 26(1):12 ([DOI](https://doi.org/10.1007/s10664-020-09909-5)) found the top causes of reviewer confusion are **missing rationale for the change** and **unfamiliarity with existing code** — both structurally worse when an agent wrote the change and you did not. **Baum, Schneider & Bacchelli (2019)** in *EMSE* 24, 1762-1798 ([DOI](https://doi.org/10.1007/s10664-018-9676-8), N=50) confirmed review is cognitively demanding in the working-memory sense and that ordering changes by relation rather than by file reduces the effort — an argument for asking agents to produce small, thematically grouped changes rather than one large correct one.

Delegating the review to a second agent has direct evidence against it. **Chowdhury, Banik, Ferdous & Shamim (2026)** at MSR '26 ([arXiv:2604.03196](https://arxiv.org/abs/2604.03196), 3,109 pull requests) found AI review agents produced a **45.2% merge rate against 68.4% for human-reviewed changes**, a 23-point gap, with 60% of closed agent-only pull requests rated as predominantly noisy feedback and a higher abandonment rate. **Gullstrand Heander, Sergeyuk, Zakharov, Söderberg & Mukhortov (2026)** ([arXiv:2606.01969](https://arxiv.org/abs/2606.01969), 17 developers plus a 43-response validation survey) found trust calibration is the dominant reviewer problem for LLM-generated multi-file changes, precisely because the author cannot be interrogated about its own confidence. Treat agent review as a noise filter that runs before you, not as a layer that replaces part of you.

On what unreviewed delegation costs in quality, **Perry, Srivastava, Kumar & Boneh (2023)** at CCS '23 ([DOI](https://doi.org/10.1145/3576915.3623157), N=47) found participants with an AI assistant wrote **significantly less secure code while being more confident it was secure** — and that the participants who trusted the assistant least and engaged most with their prompts produced the fewest vulnerabilities. **Goddard, Roudsari & Wyatt (2012)** found the same shape outside software in *JAMIA* 19(1) 121-127 ([DOI](https://doi.org/10.1136/amiajnl-2011-000089)): erroneous automated prompts raised false-positive recalls by up to 12% among 27 experienced breast-imaging radiologists.

## Skill decay is the cost that does not show up this quarter

**Arthur, Bennett, Stanush & McNelly (1998)** meta-analysed skill loss in *Human Performance* 11(1) 57-101 ([DOI](https://doi.org/10.1207/s15327043hup1101_3), 189 data points from 53 articles) and found decay reaching **d = −1.4 after a year of non-use**, with the critical qualifier that **cognitive and accuracy-based tasks decay faster than physical and speed-based ones**. Architecture judgement is a cognitive accuracy task.

**Haslbeck & Hoermann (2016)** in *Human Factors* 58(4) 533-545 ([DOI](https://doi.org/10.1177/0018720816640394), N=126 airline pilots) found that **recent practice frequency predicted manual flying skill better than total flight hours did**. Career experience does not bank against disuse; only recent practice does.

**Ericsson, Krampe & Tesch-Römer (1993)** ([DOI](https://doi.org/10.1037/0033-295X.100.3.363)) make the complementary point that maintaining an acquired skill requires continued effortful practice, and that comfortable routine execution produces **arrested development** rather than maintenance. See [[cognitive limits on deep work and recovery science]] for why the famous four-hour figure from this paper does not transfer to knowledge work, and note that the arrested-development claim is a separate observation from the contested "practice explains expertise" thesis.

This is the strongest argument for keeping a deliberate share of hands-on work, and the argument is about retained judgement rather than about throughput. If review quality depends on recognising a wrong approach quickly, and that recognition decays with disuse, then output measured this month and capability measured next year point in opposite directions.

## What actually fatigues, and what does not

**Decision fatigue in its strong form did not replicate.** **Hagger et al. (2016)** ran a 23-laboratory preregistered replication in *Perspectives on Psychological Science* 11(4) 546-573 ([DOI](https://doi.org/10.1177/1745691616652873), N=2,141) and found **d = 0.04, 95% CI [−0.07, 0.15]** against an original meta-analytic estimate near 0.62. **Vohs et al. (2021)** repeated the exercise across 36 laboratories in *Psychological Science* 32(10) 1566-1581 (N=3,531) and found a confirmatory d of 0.06 with Bayesian evidence around four to one favouring the null. The famous parole-judges result, **Danziger, Levav & Avnaim-Pesso (2011)** in *PNAS* 108(17) 6889-6892 ([DOI](https://doi.org/10.1073/pnas.1018033108)), remains contested on an unresolved case-ordering confound. The existing note [[decision fatigue]] predates this evidence and likely repeats the collapsed version.

**What does degrade is sustained evaluative attention**, which is a different mechanism with better support — the vigilance decrement in Warm, Parasuraman & Matthews above, appearing within the first half hour of monitoring and driven by resource depletion rather than by boredom. This is the fatigue your workflow actually produces, and it responds to different remedies than decision load would: shorter monitoring bouts, not fewer choices.

**Underload fatigues too.** **Poirier, Gelin & Mikolajczak (2021)** in *Frontiers in Psychology* 12:697972 ([DOI](https://doi.org/10.3389/fpsyg.2021.697972), N=507) validated **boreout** as a construct distinct from burnout, with insufficient workload and under-stimulation as separate factors. Long low-stimulation stretches — waiting on an agent, scanning correct output for a rare error — carry their own cost rather than functioning as rest.

**Recovery has the best-replicated protective evidence in this whole note.** **Sonnentag & Fritz (2007)** in *Journal of Occupational Health Psychology* 12(3) 204-221 ([DOI](https://doi.org/10.1037/1076-8998.12.3.204), N=930) validated four recovery experiences — psychological detachment, relaxation, mastery and control — and their diary follow-up work found detachment predicting next-morning positive affect and serenity, with the effect strongest after high-pressure days. Detachment means not thinking about the work, which is harder when the work is running while you sleep. See [[cognitive limits on deep work and recovery science]] for the recovery literature in more depth.

**Job resources buffer demands at the structural level.** **Lesener, Gusy & Wolter (2019)** meta-analysed 74 longitudinal studies in *Work & Stress* 33(1) 76-103 ([DOI](https://doi.org/10.1080/02678373.2018.1526065)) and found job resources explaining around 55% of variance in engagement and 52% in burnout. Autonomy over what to delegate is itself a resource, and you have more of it than most people in this literature do.

## What the evidence does not support

**Cognitive offloading is not established as harmful.** **Risko & Gilbert (2016)** in *Trends in Cognitive Sciences* 20(9) 676-688 ([DOI](https://doi.org/10.1016/j.tics.2016.07.002)) frame offloading as an adaptive strategy that people deploy sensibly based on internal-versus-external cost, not as a degradation.

**The two studies most often cited for AI harming cognition do not carry that weight.** Kosmyna et al.'s EEG study ([arXiv:2506.08872](https://arxiv.org/abs/2506.08872), N=54) is a preprint with published methodological criticism covering sample size, omitted statistics and absent correction for multiple comparisons. **Gerlich (2025)** in *Societies* 15(1):6 ([DOI](https://doi.org/10.3390/soc15010006), N=666) found a negative association between AI tool use and critical-thinking scores, but the design is correlational and is equally consistent with reverse causation.

**No study measures this workflow directly.** There is no trial of a human who writes no code, plans in natural language and reviews agent output across a multi-month horizon, and no meta-analysis comparing strain in supervisory roles against strain in individual-contributor roles. Everything above is transfer from adjacent literatures — aviation, radiology, conventional code review, AI-assisted coding — and each transfer is an argument rather than a measurement.

## What the evidence supports doing

* **Keep the veto, not just the plan.** Endsley & Kiris found intermediate control preserved situation awareness where full automation did not, so per-step consent beats reviewing a finished result.
* **Force small, thematically grouped changes.** Sadowski's Google medians and Baum's ordering result both say review effort scales badly with size, and an agent will happily produce a change larger than any human would submit.
* **Break the monitoring, not the thinking.** The vigilance decrement lands in the first 15 to 30 minutes of watching, and the underload literature says idle supervision is a cost rather than a rest.
* **Reserve a share of hands-on execution.** Haslbeck & Hoermann's recency finding is the load-bearing one — retained judgement tracks recent practice, not career totals.
* **Distrust fluency and distrust explanations.** Dzindolet found explanations raise reliance without justifying it, and Perry found the least-trusting participants produced the safest code.
