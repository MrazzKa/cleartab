-- Core schema, proposal Features 1-6. Every data table carries source_url and retrieved_at (hard rule 2).

CREATE TABLE hospitals (
    id                 serial PRIMARY KEY,
    ccn                text NOT NULL UNIQUE,
    name               text NOT NULL,
    city               text,
    metro              text CHECK (metro IN ('Tucson', 'Phoenix')),
    county             text,
    health_system      text,
    website            text,
    phone              text,
    cms_hpt_url        text,
    mrf_url            text,
    discovery_method   text,          -- cms-hpt.txt | price transparency page | manual | not found
    latitude           double precision,
    longitude          double precision,
    completeness_score numeric(5,1) CHECK (completeness_score BETWEEN 0 AND 100),
    status             text NOT NULL DEFAULT 'unknown', -- published | not published | blocked | unknown
    source_url         text,
    retrieved_at       timestamptz
);

CREATE TABLE source_files (
    id                  serial PRIMARY KEY,
    hospital_id         int NOT NULL REFERENCES hospitals(id),
    url                 text NOT NULL,
    sha256              char(64),
    size_bytes          bigint,
    format              text,          -- CMS JSON | CMS CSV tall | CMS CSV wide | non-standard
    schema_version      text,
    file_last_updated   date,
    attester_name       text,
    attestation_present boolean,
    org_npi             text,
    http_last_modified  text,
    retrieved_at        timestamptz NOT NULL,
    validator_errors    int,
    validator_warnings  int,
    source_url          text GENERATED ALWAYS AS (url) STORED,
    UNIQUE (hospital_id, sha256)
);

CREATE TABLE procedures (
    id           serial PRIMARY KEY,
    code         text NOT NULL,
    code_type    text NOT NULL CHECK (code_type IN ('CPT', 'HCPCS', 'MS-DRG')),
    plain_name   text NOT NULL,
    synonyms     text,
    description  text,
    category     text,
    setting      text,
    is_launch    boolean NOT NULL DEFAULT false,
    source_url   text,
    retrieved_at timestamptz,
    search_tsv   tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(plain_name, '') || ' ' || coalesce(synonyms, '') || ' ' ||
                               coalesce(description, '') || ' ' || code)
    ) STORED,
    UNIQUE (code, code_type)
);
CREATE INDEX procedures_tsv_idx ON procedures USING gin (search_tsv);
CREATE INDEX procedures_name_trgm_idx ON procedures USING gin (plain_name gin_trgm_ops);
CREATE INDEX procedures_syn_trgm_idx ON procedures USING gin (synonyms gin_trgm_ops);
CREATE INDEX procedures_code_trgm_idx ON procedures USING gin (code gin_trgm_ops);

CREATE TABLE payers (
    id             serial PRIMARY KEY,
    canonical_name text NOT NULL,
    plan_type      text,           -- commercial | medicare advantage | ahcccs | marketplace | other
    source_url     text,
    retrieved_at   timestamptz,
    UNIQUE (canonical_name, plan_type)
);

CREATE TABLE payer_aliases (
    id           serial PRIMARY KEY,
    raw_payer    text NOT NULL,
    raw_plan     text NOT NULL DEFAULT '',
    payer_id     int REFERENCES payers(id),   -- null = plan not matched
    method       text NOT NULL,               -- exact | regex | alias table | manual
    confidence   text,                        -- high | medium | low
    rater_status text NOT NULL DEFAULT 'provisional', -- provisional | accepted | disputed
    source_url   text,
    retrieved_at timestamptz,
    UNIQUE (raw_payer, raw_plan)
);

CREATE TABLE prices (
    id             bigserial PRIMARY KEY,
    hospital_id    int NOT NULL REFERENCES hospitals(id),
    source_file_id int NOT NULL REFERENCES source_files(id),
    procedure_id   int NOT NULL REFERENCES procedures(id),
    payer_id       int REFERENCES payers(id),     -- null for gross and cash, or plan not matched
    raw_payer      text,
    raw_plan       text,
    setting        text,                          -- inpatient | outpatient | both
    price_type     text NOT NULL CHECK (price_type IN (
                       'gross', 'cash', 'negotiated_dollar', 'negotiated_percent', 'negotiated_algorithm',
                       'allowed_median', 'allowed_p10', 'allowed_p90', 'allowed_count')),
    amount         numeric(14,2),
    percentage     numeric(10,4),
    algorithm_text text,
    methodology    text,                          -- fixed dollar | percent of charges | per diem | algorithm | ...
    flags          text[] NOT NULL DEFAULT '{}',
    source_url     text,
    retrieved_at   timestamptz
);
CREATE INDEX prices_proc_idx ON prices (procedure_id, hospital_id);
CREATE INDEX prices_file_idx ON prices (source_file_id);
CREATE INDEX prices_payer_idx ON prices (payer_id);
