from pydantic import BaseModel, Field

class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="The new role for the user (Admin or Analyst)")
