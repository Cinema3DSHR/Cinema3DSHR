# Ticket para GitHub Support — concurrencia de Actions limitada a 5 (17/11/2026)

Enviar desde la cuenta Owner de la organización en https://support.github.com/contact (categoría: GitHub Actions →
Concurrency / Runners). Texto listo para pegar (en inglés, que es lo que atiende Support):

---

**Subject:** GitHub Team organization limited to 5 concurrent Linux jobs (shows 5/60)

Hello,

Our organization **Cinema3DSHR** is on the **GitHub Team** plan. According to the Actions limits documentation, Team
allows 60 concurrent jobs on standard GitHub-hosted runners (5 of them macOS). In practice we never get more than
**5 concurrent Linux jobs**.

- Organization: `Cinema3DSHR` (plan: GitHub Team)
- Repository: `Cinema3DSHR/Cinema3DSHR` (public; transferred today, 2026-11-17, from the personal account
  `webmaletin-art`)
- Workflow run: https://github.com/Cinema3DSHR/Cinema3DSHR/actions/runs/44081670221 (workflow `episodio.yml`)
- The run has a matrix of 60 jobs, all `runs-on: ubuntu-latest`, with `strategy.max-parallel: 60`. The workflow-level
  `concurrency` group only prevents two runs of the same workflow at once; there were no other runs.
- Observed: exactly 5 jobs in progress and 55 queued for ~10 minutes. Each time one job finished, the next queued job
  started 1–2 s later, so the number of running jobs stayed at exactly 5 (a hard cap, not slow provisioning).
- Organization Settings → Actions → Runners → GitHub-hosted runners showed **"All jobs usage: 5/60"** (Linux 5,
  Windows 0, macOS 0) at the same time, so the plan limit of 60 is recognized but not used.
- For comparison, the same workflow in the personal account (GitHub Free) ran 20 jobs concurrently earlier today
  (run 44069629391, 19 render jobs simultaneous; run 44076765471, 20 simultaneous).
- The workflow file and scripts are byte-identical between the run that got 20 concurrent jobs in the personal
  account (commit d62a847) and the run limited to 5 in the organization (commit 727df1f).
- A minimal probe with no build step at all (25 jobs that only run `sleep 90`, workflow `concurrencia.yml`, run
  https://github.com/Cinema3DSHR/Cinema3DSHR/actions/runs/44084086176) also got only **6 jobs running at once** and
  19 queued, so the cap does not depend on the workload.
- No self-hosted runners, no larger runners, no macOS or Windows jobs. We did not change any spending limit.

Could you please check whether a lower concurrency limit is applied to our organization (for example because it is
new or because of the repository transfer) and raise it to the Team plan limit of 60 concurrent Linux jobs?

Thank you.

---

Qué esperar: Support confirma o levanta la restricción; después se repite la prueba de e01 (979 fotogramas, misma
configuración) y sólo vale si se ven 60 trabajos corriendo a la vez.
