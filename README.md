# Merkle Certificate Blockchain 

## What does it do?
This project implements a compact, intermediate-level blockchain for storing and verifying student certificates.
It extends a basic blockchain with Merkle trees, enabling generation and verification of Merkle inclusion proofs so a certificate's presence in a given block can be independently verified.

## How it works (brief)
1. Certificates are added as transactions (student_id, name, course, grade, issued_at).
2. Pending transactions are grouped into a block; a Merkle root of the transactions is computed and stored inside the block.
3. Mining (Proof-of-Work) finds a nonce so the block hash starts with a number of leading zeroes (configurable difficulty).
4. The block is appended to the chain and the chain is persisted to chain.json.
5. For any certificate stored in a block you can generate a Merkle proof which proves inclusion without revealing other transactions.
6. A verifier can independently check the proof against the stored Merkle root.

## Features
- Blocks with Proof-of-Work (configurable difficulty)
- Merkle tree construction and Merkle proofs for inclusion
- Generate/save proof to a JSON file for independent verification
- Verify Merkle proofs from a proof file
- Persistent chain storage (chain.json) and chain export
- Single-file Python project, only uses the standard library

## How to run
1. Save the single-file script `merkle_certificate_blockchain.py` in a folder.
2. Run:
```bash
python merkle_certificate_blockchain.py
```
3. Use the menu to add certificates, mine, generate Merkle proofs, verify proofs, and export the chain.

## Files produced at runtime
- `chain.json` — persistent chain storage
- `merkle_proof_b{block}_t{tx}.json` — Merkle proof JSON output
- `chain_export.json` — optional chain export

## Why this is good for assignment
- Demonstrates core blockchain concepts (PoW) and deeper concepts (Merkle trees & proofs)
- Single-file, easy to submit and run
- Produces verifiable artifacts (proof JSON + chain) that examiners can inspect
