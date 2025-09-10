
from app import app, db
from sqlalchemy import text

def migrate_allocation_status():
    with app.app_context():
        try:
            print("Iniciando migração da tabela allocations...")
            
            # Verificar se as colunas já existem
            columns_to_add = [
                ('status', 'VARCHAR(20)', 'pending'),
                ('approved_by_id', 'INTEGER', None),
                ('approved_at', 'TIMESTAMP', None),
                ('approval_notes', 'TEXT', None)
            ]
            
            for column_name, column_type, default_value in columns_to_add:
                # Verificar se a coluna existe
                result = db.session.execute(
                    text(f"SELECT column_name FROM information_schema.columns WHERE table_name='allocations' AND column_name='{column_name}'")
                )
                
                if not result.fetchone():
                    print(f"Adicionando coluna {column_name}...")
                    
                    # Adicionar a coluna
                    if column_name == 'approved_by_id':
                        db.session.execute(
                            text(f"ALTER TABLE allocations ADD COLUMN {column_name} {column_type} REFERENCES users(id)")
                        )
                    else:
                        db.session.execute(
                            text(f"ALTER TABLE allocations ADD COLUMN {column_name} {column_type}")
                        )
                    
                    # Definir valor padrão se necessário
                    if default_value:
                        db.session.execute(
                            text(f"UPDATE allocations SET {column_name} = '{default_value}' WHERE {column_name} IS NULL")
                        )
                        
                        # Tornar a coluna NOT NULL para status
                        if column_name == 'status':
                            db.session.execute(
                                text(f"ALTER TABLE allocations ALTER COLUMN {column_name} SET NOT NULL")
                            )
                    
                    print(f"Coluna {column_name} adicionada com sucesso!")
                else:
                    print(f"Coluna {column_name} já existe.")
            
            # Para allocations existentes, marcar como 'approved' se não tiverem status
            db.session.execute(
                text("UPDATE allocations SET status = 'approved' WHERE status IS NULL")
            )
            
            db.session.commit()
            print("Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    migrate_allocation_status()
