

import hashlib, json, time, os, math
from typing import List, Tuple, Dict

CHAIN_FILE = "chain.json"
DIFFICULTY = 3  

def sha256(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()

def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()


def merkle_layers(items: List[dict]) -> List[List[str]]:
    """Return Merkle tree layers from leaves to root (list of lists of hex hashes)."""
    leaves = [sha256(canonical(x)) for x in items] or [sha256(b'')]
    layers = [leaves]
    while len(layers[-1]) > 1:
        prev = layers[-1]
        if len(prev) % 2 == 1:
            prev = prev + [prev[-1]]
        nxt = []
        for i in range(0, len(prev), 2):
            a, b = prev[i], prev[i+1]
            nxt.append(sha256((a + b).encode()))
        layers.append(nxt)
    return layers

def merkle_root(items: List[dict]) -> str:
    return merkle_layers(items)[-1][0]

def merkle_proof(items: List[dict], index: int) -> List[Tuple[str, str]]:
   
    layers = merkle_layers(items)
    proof = []
    idx = index
    for layer in layers[:-1]:
        # ensure even
        l = layer if len(layer) % 2 == 0 else layer + [layer[-1]]
        sibling_index = idx ^ 1
        sibling_hash = l[sibling_index]
        direction = 'L' if sibling_index < idx else 'R'
        proof.append((sibling_hash, direction))
        idx = idx // 2
    return proof

def verify_merkle_proof(leaf: dict, proof: List[Tuple[str,str]], root: str) -> bool:
    h = sha256(canonical(leaf))
    for sibling_hash, direction in proof:
        if direction == 'L':
            h = sha256((sibling_hash + h).encode())
        else:
            h = sha256((h + sibling_hash).encode())
    return h == root

class Block:
    def __init__(self, index:int, transactions:List[dict], timestamp:float, previous_hash:str, nonce:int=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.merkle_root = merkle_root(transactions)
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        obj = {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root
        }
        return sha256(canonical(obj))

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(d: dict):
        b = Block(d["index"], d["transactions"], d["timestamp"], d["previous_hash"], d.get("nonce",0))
        # override computed values with stored values to avoid re-mining
        b.merkle_root = d.get("merkle_root", b.merkle_root)
        b.hash = d.get("hash", b.compute_hash())
        return b

class Blockchain:
    def __init__(self, difficulty:int = DIFFICULTY):
        self.difficulty = difficulty
        self.unconfirmed_transactions: List[dict] = []
        self.chain: List[Block] = []
        self.load_chain()

    def create_genesis(self):
        genesis = Block(0, [], time.time(), "0", nonce=0)
        genesis.hash = genesis.compute_hash()
        self.chain = [genesis]
        self.save_chain()

    def load_chain(self):
        if os.path.exists(CHAIN_FILE):
            with open(CHAIN_FILE, "r") as f:
                data = json.load(f)
            self.chain = [Block.from_dict(b) for b in data]
            if not self.chain:
                self.create_genesis()
        else:
            self.create_genesis()

    def save_chain(self):
        with open(CHAIN_FILE, "w") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=2)

    def add_transaction(self, student_id:str, name:str, course:str, grade:str):
        tx = {
            "student_id": student_id,
            "name": name,
            "course": course,
            "grade": grade,
            "issued_at": int(time.time())
        }
        # simple duplicate prevention within pending txs
        for t in self.unconfirmed_transactions:
            if t["student_id"] == student_id and t["course"] == course:
                return False
        self.unconfirmed_transactions.append(tx)
        return True

    def last_block(self) -> Block:
        return self.chain[-1]

    def proof_of_work(self, block: Block) -> str:
        target = "0" * self.difficulty
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block.hash

    def mine(self) -> Tuple[bool, Block]:
        if not self.unconfirmed_transactions:
            return False, None
        last = self.last_block()
        new_block = Block(last.index + 1, list(self.unconfirmed_transactions), time.time(), last.hash, nonce=0)
        self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.unconfirmed_transactions = []
        self.save_chain()
        return True, new_block

    def find_certificate_location(self, student_id:str, course:str) -> Tuple[int,int]:
        """
        Find certificate in chain.
        Returns (block_index, tx_index) or (-1,-1) if not found.
        """
        for b in self.chain:
            for i,tx in enumerate(b.transactions):
                if tx["student_id"] == student_id and tx["course"] == course:
                    return b.index, i
        return -1, -1

    def get_block_by_index(self, index:int) -> Block:
        for b in self.chain:
            if b.index == index:
                return b
        return None

# -------------------- CLI --------------------
def pretty_print_block(b: Block):
    print(f"\n--- Block {b.index} ---")
    print(f"Timestamp    : {time.ctime(b.timestamp)}")
    print(f"Previous Hash: {b.previous_hash}")
    print(f"Nonce        : {b.nonce}")
    print(f"Merkle Root  : {b.merkle_root}")
    print(f"Hash         : {b.hash}")
    print("Transactions :")
    if not b.transactions:
        print("  (no transactions)")
    for idx,tx in enumerate(b.transactions):
        print(f"  [{idx}] {tx}")

def menu():
    bc = Blockchain()
    while True:
        print("\n===== Merkle Certificate Blockchain =====")
        print("1. Add certificate (pending)")
        print("2. Mine pending certificates")
        print("3. View full chain")
        print("4. Generate Merkle proof for a certificate")
        print("5. Verify a Merkle proof from file")
        print("6. Export chain to JSON")
        print("7. Exit")
        ch = input("Choice: ").strip()
        if ch == "1":
            sid = input("Student ID: ").strip()
            name = input("Name: ").strip()
            course = input("Course: ").strip()
            grade = input("Grade: ").strip()
            ok = bc.add_transaction(sid, name, course, grade)
            print("Added to pending." if ok else "Duplicate pending certificate found; not added.")
        elif ch == "2":
            ok, blk = bc.mine()
            if not ok:
                print("No pending certificates to mine.")
            else:
                print(f"Block mined! Index: {blk.index}, Hash: {blk.hash}")
        elif ch == "3":
            for b in bc.chain:
                pretty_print_block(b)
        elif ch == "4":
            sid = input("Student ID: ").strip()
            course = input("Course: ").strip()
            b_index, tx_index = bc.find_certificate_location(sid, course)
            if b_index == -1:
                print("Certificate not found in chain.")
            else:
                block = bc.get_block_by_index(b_index)
                proof = merkle_proof(block.transactions, tx_index)
                proof_obj = {
                    "block_index": block.index,
                    "tx_index": tx_index,
                    "transaction": block.transactions[tx_index],
                    "merkle_root": block.merkle_root,
                    "proof": proof
                }
                fname = f"merkle_proof_b{block.index}_t{tx_index}.json"
                with open(fname, "w") as f:
                    json.dump(proof_obj, f, indent=2)
                print(f"Merkle proof saved to {fname}. You can submit this proof for independent verification.")
                print("Proof content (short):")
                print(json.dumps({"block": block.index, "tx_index": tx_index, "merkle_root": block.merkle_root}, indent=2))
        elif ch == "5":
            fname = input("Proof file path: ").strip()
            if not os.path.exists(fname):
                print("File not found.")
            else:
                with open(fname, "r") as f:
                    p = json.load(f)
                leaf = p["transaction"]
                proof = p["proof"]
                root = p["merkle_root"]
                ok = verify_merkle_proof(leaf, proof, root)
                print("✅ Proof VERIFIED — certificate is included in the block." if ok else "❌ Proof INVALID.")
        elif ch == "6":
            out = input("Output filename (default chain_export.json): ").strip() or "chain_export.json"
            with open(out, "w") as f:
                json.dump([b.to_dict() for b in bc.chain], f, indent=2)
            print(f"Chain exported to {out}")
        elif ch == "7":
            print("Bye.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    menu()
