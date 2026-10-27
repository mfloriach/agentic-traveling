import asyncio
from dataclasses import dataclass
from typing import Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

load_dotenv()

@dataclass
class Patient:
    id: int
    name: str
    vitals: dict[str, Any]
    
PATIENT_DB = {
    42: Patient(id=42, name="John Doe", vitals={"heat_rate": 72}),
    43: Patient(id=43, name="Pedro", vitals={"heat_rate": 72}),
    44: Patient(id=44, name="Marti", vitals={"heat_rate": 72}),
    45: Patient(id=45, name="Jeniffer", vitals={"heat_rate": 72}),
}

class DatabaseConn:
    async def patient_name(self, id: int) -> str:
        patient = PATIENT_DB.get(id)
        return patient.name if patient else "Unknown Patient"
    
    async def latest_vitals(self, id: int) -> dict[str, Any]:
        patient = PATIENT_DB.get(id)
        return patient.vitals if patient else "Unknown Patient"
    
@dataclass
class TriageDependencies:
    patient_id: int
    db: DatabaseConn
    
class TriageOutput(BaseModel):
    response_text: str = Field(description="Message to the patient")
    escalate: bool = Field(description="Whether to escalate the case")
    urgency: int = Field(description="Urgency level of the case")
    
triage_agent = Agent(
    name="triage_agent",
    description="medical advice base on the patient",
    dependencies=TriageDependencies,
    output_model= TriageOutput,
    model="openai:gpt-4o",
    max_concurrency=10,
    max_token=1000,
    temperature=0.5,
    system_prompt=(
        "You are a triaged assistant helping patients."
        "Provide clear advice and assess urgency."
        "Always mention the patient's name whe available"
    )
)

@triage_agent.system_prompt
async def add_patient_name(ctx: RunContext[TriageDependencies]) -> str:
    patient_name = await ctx.deps.db.patient_name(ctx.deps.patient_id)
    return f"Patient Name: {patient_name}"

@triage_agent.tool
async def get_latest_vitals(ctx: RunContext[TriageDependencies]) -> dict[str, Any]:
    return await ctx.deps.db.latest_vitals(ctx.deps.patient_id)

async def main() -> None:
    deps = TriageDependencies(
        patient_id=42,
        db=DatabaseConn()
    )
    
    result = await triage_agent.run(
        "What should I do if I have a headache and a fever?",
        deps=deps
    )
    
    print(result.output)
    
    
if __name__ == "__main__":
    asyncio.run(main())