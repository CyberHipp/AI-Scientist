# Anthrobots and the Bioelectric "Anatomical Compiler": Why Motile Human-Cell Collectives Reframe Regenerative Medicine, Biohybrid Robotics, and Combination-Product Regulation

**Nature-style Perspective**

## Standfirst

Anthrobots—motile multicellular constructs self-assembled from adult human airway epithelial cells without genetic engineering—bring Michael Levin’s thesis into a human-cell substrate: that anatomical outcomes are governed by controllable, distributed information processing (including bioelectric state) rather than DNA sequence alone. Their reported behavioral heterogeneity and in-vitro neural "scratch" repair effects make them scientifically provocative, translationally tempting, and regulatorily non-trivial—especially once delivery devices, scaffolds, encapsulation systems, or digital control layers are integral to their intended clinical function.

## A new class of human-cell "agents"

The primary anthrobot literature reports that adult human airway epithelial cells can self-construct into small, cilia-driven motile multicellular bodies with diverse morphologies and movement modes, and—under defined in-vitro conditions—these constructs can traverse cultured human neural sheets and accelerate closure of scratch defects. A 2025 follow-on paper describes a morphological/behavioral/transcriptomic "life cycle" with substantial gene-expression remodeling relative to source cells, consistent with a system-level state transition rather than a superficial rearrangement.

**Why this matters:** if adult somatic cells can be coaxed into coherent, functional collectives without genomic editing, then the operational "program" of tissue can be shifted by changing boundary conditions and network state. This aligns with Michael Levin’s broader argument: multicellular patterning and repair reflect distributed control (bioelectric, biochemical, mechanical) that encodes and enacts anatomical goals.

## Levin’s bioelectric code meets a human substrate

Levin’s "bioelectric code" framing treats resting membrane potentials, ion channel dynamics, and gap-junction coupling as a computational medium capable of storing "pattern memories" and guiding morphogenesis and regeneration. Anthrobots can be read as a competency demonstration: a human-cell collective (i) forms a stable morphology, (ii) generates macroscopic movement via coordinated cilia, and (iii) interacts with damage contexts in ways correlated with repair-associated effects. Regardless of whether one labels this "basal cognition" or "high-dimensional control," anthrobots provide a concrete testbed for the hypothesis that morphological outcomes are attractors—and that bioelectric state, mechanics, and geometry are actionable control knobs for moving between attractors.

## Translational promise: behavior as the active ingredient

Most cell therapies treat cells as factories (secreting factors) or building blocks (forming tissue). Anthrobots introduce a third category: **cells as embodied agents** where behavior—migration, coverage, mechanical interaction—may be part of the therapeutic mechanism. That shift changes potency definitions: if the clinical hypothesis is "anthrobots improve repair by doing X in situ," then release criteria must include behavioral assays with defined endpoints, acceptable variance, and failure signatures, not just marker panels.

Translation bottlenecks to expect and measure:

- **Batch heterogeneity:** movement phenotypes and lifetimes may vary by donor, culture conditions, and assembly geometry.
- **State drift:** transcriptomic remodeling implies that anthrobot identity changes over time; stability windows must be defined.
- **Mechanism uncertainty:** repair-associated effects in vitro are not yet a clinical mechanism; assays need causal dissection (contact vs. secretome vs. mechanical effects).

## Safety and containment: new failure modes

Safety considerations extend beyond toxicity to misbehavior under distribution shift: unexpected persistence, aggregation, migration or occlusion risks, immune interactions, and phenotype switching. A pragmatic posture is to treat anthrobots as high-variance agents until proven otherwise: require pre-registered behavioral endpoints, explicit kill conditions in assays, and documented failure modes as first-class outputs.

## Regulatory intersections: ATMPs, devices, and combination products

### EU: combined ATMPs and MDR entanglements

Regulation (EC) No 1394/2007 governs advanced therapy medicinal products (ATMPs) and explicitly contemplates **combined ATMPs** where a medical device is integral. When viable cells or tissues drive the principal action, the ATMP framework applies even if a device component is essential. Device intersections become unavoidable when delivery systems, scaffolds/matrices, encapsulation hardware, or software-driven control/monitoring are integral to the intended function. EMA’s Article 9 consultation process for Notified Body input exists to assess device components within ATMP evaluations, and MDR (Regulation (EU) 2017/745) introduces additional requirements—such as Notified Body opinions for certain integral devices—often operationalized via MDR Article 117 pathways.

### US: combination-product assignment and HCT/P boundaries

In the United States, products that combine regulated article types may be treated as **combination products**, triggering jurisdiction assignment under 21 CFR Part 3 and manufacturing expectations in 21 CFR Part 4. Anthrobot-based interventions framed as engineered therapeutics are unlikely to qualify as narrowly defined 361 HCT/Ps because minimal manipulation and homologous-use criteria would be exceeded. When a delivery or containment device is essential to the intended function, sponsors should anticipate early inquiries about primary mode of action, Center assignment (CBER vs. CDRH), and how biologics CMC expectations will be reconciled with device design controls.

## Outlook: toward an anatomical compiler with a quality system

Levin’s longer-term vision is an "anatomical compiler" that lets us specify target outcomes and reliably steer living matter. Anthrobots make this concrete within a human-cell substrate but also expose governance debt. Progress depends on standardized evaluation, traceability, and combined-product regulatory design—not just conceptual elegance.

---

# Appendix A — EvalOps Spec (YAML) for Living-Construct Evaluation

This appendix provides repo-ready schemas and default policies you can validate in CI.

## A1. Recommended layout

```
evalops/
  schemas/
    protocol.schema.yaml
    run.schema.yaml
    artifact-policy.schema.yaml
    dataset.schema.yaml
    metrics.schema.yaml
  policies/
    artifact_policy.default.yaml
    privacy_policy.default.yaml
  protocols/
    scratch_repair_v1.protocol.yaml
    motility_arena_v1.protocol.yaml
  datasets/
    neural_sheet_fixture_v1.dataset.yaml
  runs/
    2025-12-10T104314Z_run01.run.yaml
```

## A2. `protocol.schema.yaml`

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: EvalOps Protocol Schema
type: object
required: [protocol_id, version, kind, objective, endpoints, materials, procedure, instrumentation, analysis, safety_gates]
properties:
  protocol_id:
    type: string
    pattern: "^[a-z0-9_\-]+$"
  version:
    type: string
    pattern: "^v\d+\.\d+(\.\d+)?$"
  kind:
    type: string
    enum: [motility, repair_assay, secretion, stability, containment, device_integration, software_control]
  objective:
    type: string
    minLength: 10
  endpoints:
    type: array
    minItems: 1
    items:
      type: object
      required: [name, type, unit, primary, preregistered, computation]
      properties:
        name: { type: string }
        type: { type: string, enum: [continuous, categorical, time_to_event, boolean] }
        unit: { type: string }
        primary: { type: boolean }
        preregistered: { type: boolean, const: true }
        computation:
          type: object
          required: [method, inputs, output]
          properties:
            method: { type: string }
            inputs: { type: array, items: { type: string } }
            output: { type: string }
  materials:
    type: object
    required: [cell_source, media, substrates]
    properties:
      cell_source:
        type: object
        required: [species, tissue, donor_bucket, manipulation_summary]
        properties:
          species: { type: string, enum: [human, mouse, frog, other] }
          tissue: { type: string }
          donor_bucket:
            description: "Non-identifying bucket (no direct identifiers)."
            type: object
            required: [age_range, sex, comorbidity_flags]
            properties:
              age_range: { type: string, pattern: "^\d+\-\d+$" }
              sex: { type: string, enum: [female, male, intersex, unknown] }
              comorbidity_flags: { type: array, items: { type: string } }
          manipulation_summary: { type: string }
      media: { type: array, items: { type: string } }
      substrates: { type: array, items: { type: string } }
  procedure:
    type: array
    minItems: 3
    items:
      type: object
      required: [step, action, params]
      properties:
        step: { type: integer, minimum: 1 }
        action: { type: string }
        params: { type: object }
  instrumentation:
    type: object
    required: [imaging, environment_control]
    properties:
      imaging: { type: object }
      environment_control: { type: object }
  analysis:
    type: object
    required: [software, metrics, statistics]
    properties:
      software: { type: array, items: { type: string } }
      metrics: { type: array, items: { type: string } }
      statistics:
        type: object
        required: [design, tests, multiple_comparisons]
        properties:
          design: { type: string, enum: [paired, unpaired, longitudinal, factorial] }
          tests: { type: array, items: { type: string } }
          multiple_comparisons: { type: string }
  safety_gates:
    type: array
    items:
      type: object
      required: [name, metric, threshold, operator, on_fail]
      properties:
        name: { type: string }
        metric: { type: string }
        threshold: { type: number }
        operator: { type: string, enum: ["<", "<=", ">", ">=", "=="] }
        on_fail: { type: string, enum: [halt, quarantine, repeat, escalate_review] }
```

## A3. `artifact-policy.schema.yaml`

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: EvalOps Artifact Policy Schema
type: object
required: [policy_id, defaults, allowlist, denylist, retention]
properties:
  policy_id: { type: string }
  defaults:
    type: object
    required: [store_raw_outputs, store_aggregates, store_hashes_only]
    properties:
      store_raw_outputs:
        description: "Must be false for internal/sensitive evals."
        type: boolean
      store_aggregates: { type: boolean }
      store_hashes_only: { type: boolean }
  allowlist:
    type: array
    items:
      type: object
      required: [artifact_type, storage_class, redaction]
      properties:
        artifact_type:
          type: string
          enum: [metrics_json, summary_csv, run_manifest, protocol_copy, model_card, plots_png, logs_text]
        storage_class: { type: string, enum: [public, internal, restricted] }
        redaction: { type: string, enum: [none, remove_ids, aggregate_only] }
  denylist:
    type: array
    items:
      type: string
      enum: [raw_images, raw_video, raw_transcriptomics_fastq, donor_identifiers, raw_text_outputs]
  retention:
    type: object
    required: [days_internal, days_restricted, delete_on_request]
    properties:
      days_internal: { type: integer, minimum: 1 }
      days_restricted: { type: integer, minimum: 1 }
      delete_on_request: { type: boolean }
```

## A4. Default artifact policy (`policies/artifact_policy.default.yaml`)

```yaml
policy_id: "default_no_raw_outputs_v1"
defaults:
  store_raw_outputs: false
  store_aggregates: true
  store_hashes_only: true

allowlist:
  - artifact_type: "metrics_json"
    storage_class: "internal"
    redaction: "aggregate_only"
  - artifact_type: "summary_csv"
    storage_class: "internal"
    redaction: "aggregate_only"
  - artifact_type: "run_manifest"
    storage_class: "internal"
    redaction: "remove_ids"
  - artifact_type: "protocol_copy"
    storage_class: "internal"
    redaction: "none"
  - artifact_type: "model_card"
    storage_class: "internal"
    redaction: "remove_ids"

denylist:
  - "raw_images"
  - "raw_video"
  - "raw_transcriptomics_fastq"
  - "donor_identifiers"
  - "raw_text_outputs"

retention:
  days_internal: 365
  days_restricted: 90
  delete_on_request: true
```

## A5. `run.schema.yaml`

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: EvalOps Run Manifest Schema
type: object
required: [run_id, timestamp_utc, protocol_ref, dataset_ref, environment, operators, artifacts, results]
properties:
  run_id: { type: string, pattern: "^[A-Z0-9_\-]+$" }
  timestamp_utc: { type: string, format: date-time }
  protocol_ref:
    type: object
    required: [protocol_id, version, sha256]
    properties:
      protocol_id: { type: string }
      version: { type: string }
      sha256: { type: string, pattern: "^[a-f0-9]{64}$" }
  dataset_ref:
    type: object
    required: [dataset_id, version, sha256]
    properties:
      dataset_id: { type: string }
      version: { type: string }
      sha256: { type: string, pattern: "^[a-f0-9]{64}$" }
  environment:
    type: object
    required: [os, container_image, package_lock, hardware]
    properties:
      os: { type: string }
      container_image: { type: string }
      package_lock: { type: string }
      hardware:
        type: object
        required: [cpu, ram_gb, gpu, microscope, incubator]
        properties:
          cpu: { type: string }
          ram_gb: { type: number }
          gpu: { type: array, items: { type: string } }
          microscope: { type: string }
          incubator: { type: string }
  operators:
    type: array
    items:
      type: object
      required: [role, pseudonym, signoff]
      properties:
        role: { type: string }
        pseudonym: { type: string }
        signoff: { type: string, enum: [approved, needs_review, rejected] }
  artifacts:
    type: object
    required: [artifact_policy_id, stored]
    properties:
      artifact_policy_id: { type: string }
      stored:
        type: array
        items:
          type: object
          required: [artifact_type, sha256, location]
          properties:
            artifact_type: { type: string }
            sha256: { type: string, pattern: "^[a-f0-9]{64}$" }
            location: { type: string }
  results:
    type: object
    required: [metrics, safety_gates, notes]
    properties:
      metrics: { type: object, additionalProperties: { type: number } }
      safety_gates:
        type: array
        items:
          type: object
          required: [name, passed, value]
          properties:
            name: { type: string }
            passed: { type: boolean }
            value: { type: number }
      notes: { type: string }
```

## A6. Example protocol (`protocols/scratch_repair_v1.protocol.yaml`)

```yaml
protocol_id: "scratch_repair_neural_sheet"
version: "v1.0"
kind: "repair_assay"
objective: "Quantify closure acceleration of standardized scratch defects in cultured human neural sheets under anthrobot exposure."
endpoints:
  - name: "closure_rate"
    type: "continuous"
    unit: "% area/hr"
    primary: true
    preregistered: true
    computation:
      method: "segmented_area_time_series"
      inputs: ["timepoint_masks"]
      output: "slope_percent_per_hour"
  - name: "time_to_95pct"
    type: "time_to_event"
    unit: "hours"
    primary: false
    preregistered: true
    computation:
      method: "threshold_crossing"
      inputs: ["closure_curve"]
      output: "t_95"

materials:
  cell_source:
    species: "human"
    tissue: "airway_epithelium"
    donor_bucket:
      age_range: "20-40"
      sex: "unknown"
      comorbidity_flags: []
    manipulation_summary: "Self-assembly under defined culture geometry; no genetic modification."
  media: ["defined_media_A", "neural_sheet_media_B"]
  substrates: ["coated_glass", "standard_plate"]

procedure:
  - step: 1
    action: "prepare_neural_sheet"
    params: { plating_density: "X", maturation_days: 7 }
  - step: 2
    action: "create_scratch"
    params: { tool: "standard_scratch_tip", width_um: 300 }
  - step: 3
    action: "add_constructs"
    params: { constructs_per_well: 10, exposure_hours: 48 }
  - step: 4
    action: "time_lapse_imaging"
    params: { interval_min: 10, duration_hr: 48 }

instrumentation:
  imaging: { modality: "phase_contrast", objective: "10x", frame_rate: "per_interval" }
  environment_control: { temp_c: 37, co2_pct: 5, humidity: "high" }

analysis:
  software: ["segmentation_pipeline_v1", "metrics_calc_v1"]
  metrics: ["closure_rate", "time_to_95pct"]
  statistics:
    design: "unpaired"
    tests: ["bootstrap_CI", "permutation_test"]
    multiple_comparisons: "BH-FDR"

safety_gates:
  - name: "construct_overgrowth"
    metric: "max_construct_area_fraction"
    threshold: 0.20
    operator: "<="
    on_fail: "halt"
```
