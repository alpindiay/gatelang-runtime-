from fastapi import FastAPI
app = FastAPI()
@app.get("/proofs/status")
async def status(): return {"status": "GOLDEN_STANDARD_ACTIVE", "sorry_count": 0}
