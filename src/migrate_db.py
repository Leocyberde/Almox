
from app import app, db
from models import Product
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        try:
            # Verificar se a coluna supplier_id ainda existe
            result = db.session.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name='products' AND column_name='supplier_id'")
            )
            
            if result.fetchone():
                print("Removendo coluna supplier_id obsoleta...")
                
                # Remover a constraint de foreign key primeiro (se existir)
                try:
                    db.session.execute(
                        text("ALTER TABLE products DROP CONSTRAINT IF EXISTS products_supplier_id_fkey")
                    )
                except:
                    pass
                
                # Remover a coluna supplier_id
                db.session.execute(
                    text("ALTER TABLE products DROP COLUMN IF EXISTS supplier_id")
                )
                
                print("Coluna supplier_id removida com sucesso!")
            
            # Verificar se a coluna supplier_name existe
            result = db.session.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name='products' AND column_name='supplier_name'")
            )
            
            if not result.fetchone():
                print("Adicionando coluna supplier_name...")
                
                # Adicionar a coluna supplier_name
                db.session.execute(
                    text("ALTER TABLE products ADD COLUMN supplier_name VARCHAR(100)")
                )
                
                # Definir um valor padrão para registros existentes
                db.session.execute(
                    text("UPDATE products SET supplier_name = 'Fornecedor não informado' WHERE supplier_name IS NULL")
                )
                
                # Tornar a coluna NOT NULL
                db.session.execute(
                    text("ALTER TABLE products ALTER COLUMN supplier_name SET NOT NULL")
                )
                
                print("Coluna supplier_name adicionada com sucesso!")
            else:
                print("Coluna supplier_name já existe.")
            
            db.session.commit()
            print("Migração concluída com sucesso!")
                
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    migrate_database()
