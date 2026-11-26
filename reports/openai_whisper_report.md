# Compliance Report: openai/whisper

- **Repository:** [openai/whisper](https://github.com/openai/whisper)
- **Question:** Run a full compliance assessment across all governance controls.

## Answer

A full compliance assessment across all 5 AI governance controls was performed on the 'openai/whisper' repository. The repository passes 4 controls (Documentation, Licensing, Model Documentation, and AI Transparency) and fails 1 control (Security) due to the absence of a repository-level or organization-level security policy.

## Executive Summary

openai/whisper satisfies controls for Documentation (comprehensive README.md), Licensing (MIT License), Model Documentation (dedicated model-card.md), and AI Transparency (explicit intended uses, out-of-scope uses, and detailed limitations). However, it fails the Security control because no SECURITY.md file was found either within the repository or in the organization .github repository.

| Control | Status | Sources |
| --- | --- | --- |
| Documentation | **PASS** | [link](https://github.com/openai/whisper/blob/main/README.md) |
| Licensing | **PASS** | [link](https://github.com/openai/whisper), [link](https://github.com/openai/whisper/blob/main/LICENSE) |
| Model Documentation | **PASS** | [link](https://github.com/openai/whisper/blob/main/model-card.md) |
| AI Transparency | **PASS** | [link](https://github.com/openai/whisper/blob/main/model-card.md) |
| Security | **FAIL** | [link](https://github.com/openai/whisper/tree/main), [link](https://github.com/openai/.github) |

## Detailed Control Evaluations

### Documentation — PASS
**Description:** Does the repository contain a nonempty README file?

**Explanation:** A nonempty README.md is present in the repository root containing overview, installation setup, model size details, and CLI/Python usage instructions.

**Supporting Evidence:**
- Repository contains a substantive README.md file (size 8246 bytes).
- README.md begins with: '# Whisper\n\n[[Blog]](https://openai.com/blog/whisper)\n[[Paper]](https://arxiv.org/abs/2212.04356)... Whisper is a general-purpose speech recognition model.'

**Source References:**
- https://github.com/openai/whisper/blob/main/README.md

### Licensing — PASS
**Description:** Does the repository use an approved license (MIT or Apache 2.0)?

**Explanation:** The repository uses the MIT license, which is one of the approved open-source licenses.

**Supporting Evidence:**
- Repository metadata confirms license SPDX identifier 'MIT'.
- LICENSE file at root contains full MIT License text: 'MIT License\n\nCopyright (c) 2022 OpenAI\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software...'

**Source References:**
- https://github.com/openai/whisper
- https://github.com/openai/whisper/blob/main/LICENSE

### Model Documentation — PASS
**Description:** Does the repository contain a model card?

**Explanation:** The repository includes a dedicated model-card.md documenting model specifications, sizes, training data, and release history.

**Supporting Evidence:**
- Repository contains dedicated file 'model-card.md' at the root.
- model-card.md states: '# Model Card: Whisper\n\nThis is the official codebase for running the automatic speech recognition (ASR) models (Whisper models) trained and released by OpenAI. Following Model Cards for Model Reporting (Mitchell et al.), we\'re providing some information about the automatic speech recognition model.'

**Source References:**
- https://github.com/openai/whisper/blob/main/model-card.md

### AI Transparency — PASS
**Description:** Are the model's intended use and limitations adequately documented?

**Explanation:** The model card explicitly outlines intended users and applications, cautions against unapproved high-risk uses, and provides detailed documentation of known limitations such as hallucinations, language discrepancies, and demographic disparities.

**Supporting Evidence:**
- model-card.md 'Model Use / Evaluated Use' section specifies: 'The primary intended users of these models are AI researchers studying the robustness, generalization, capabilities, biases, and constraints of the current model. However, Whisper is also potentially quite useful as an ASR solution for developers, especially for English speech recognition.'
- model-card.md cautions against out-of-scope uses: 'In particular, we caution against using Whisper models to transcribe recordings of individuals taken without their consent or purporting to use these models for any kind of subjective classification. We recommend against use in high-risk domains like decision-making contexts...'
- model-card.md 'Performance and Limitations' section documents: 'because the models are trained in a weakly supervised manner using large-scale noisy data, the predictions may include texts that are not actually spoken in the audio input (i.e. hallucination)... The models also exhibit disparate performance on different accents and dialects of particular languages, which may include a higher word error rate across speakers of different genders, races, ages, or other demographic criteria.'

**Source References:**
- https://github.com/openai/whisper/blob/main/model-card.md

### Security — FAIL
**Description:** Does the repository contain a security policy?

**Explanation:** Neither repository-level security documentation nor an organization-level default security policy could be located.

**Supporting Evidence:**
- Repository file listing from https://github.com/openai/whisper/tree/main does not contain SECURITY.md, .github/SECURITY.md, or docs/SECURITY.md.
- Organization-level check at https://github.com/openai/.github checked paths 'SECURITY.md' and '.github/SECURITY.md' and returned 'found: false'.

**Source References:**
- https://github.com/openai/whisper/tree/main
- https://github.com/openai/.github

**Recommended Remediation:** Add a SECURITY.md file to the repository root or .github directory detailing vulnerability reporting guidelines and supported versions.

## Agent Evidence Collection Trace

- `get_repo_metadata({})` [OK]: Metadata loaded (branch=main, license=MIT).
- `list_repo_files({})` [OK]: Listed 45 paths (total 45).
- `read_repo_file({'path': 'README.md'})` [OK]: Read README.md (8243 chars).
- `read_repo_file({'path': 'LICENSE'})` [OK]: Read LICENSE (1063 chars).
- `read_repo_file({'path': 'model-card.md'})` [OK]: Read model-card.md (7279 chars).
- `check_org_security_policy({})` [OK]: No org-level security policy found.
