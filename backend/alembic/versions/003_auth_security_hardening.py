
from alembic import op
import sqlalchemy as sa


                                        
revision = '003_auth_security_hardening'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('avatar', sa.String(500), nullable=True))
    op.add_column('users', sa.Column(
        'provider', sa.String(50), nullable=False, server_default='credentials'
    ))
    
                                              
                                             
    op.execute("UPDATE users SET role = 'Analyst' WHERE role = 'Data_Scientist'")
    
                                         
                                                                                   
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    
                                                 
    user_role_new = sa.Enum('Admin', 'Analyst', name='user_role')
    user_role_new.create(op.get_bind(), checkfirst=True)
    
                                  
    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN role TYPE user_role "
        "USING role::text::user_role"
    )
    
                                       
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'Analyst'")
    
                        
    op.execute("DROP TYPE user_role_old")
    
                                                                
    op.alter_column('users', 'password_hash', nullable=True)


def downgrade() -> None:
    op.execute(
        "UPDATE users SET password_hash = '$2b$12$placeholder' "
        "WHERE password_hash IS NULL"
    )
    op.alter_column('users', 'password_hash', nullable=False)
    
                                                  
    op.execute("ALTER TYPE user_role RENAME TO user_role_new")
    
    user_role_old = sa.Enum('Admin', 'Data_Scientist', 'Analyst', name='user_role')
    user_role_old.create(op.get_bind(), checkfirst=True)
    
    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN role TYPE user_role "
        "USING role::text::user_role"
    )
    
    op.execute("DROP TYPE user_role_new")
    
                                
    op.drop_column('users', 'provider')
    op.drop_column('users', 'avatar')
    op.drop_column('users', 'name')
