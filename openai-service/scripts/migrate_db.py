import argparse
from pymongo import MongoClient
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_data(source_uri: str, target_uri: str, database: str):
    """Migrate data from source to target MongoDB"""
    try:
        # Connect to both databases
        source_client = MongoClient(source_uri)
        target_client = MongoClient(target_uri)

        # Get database handles
        source_db = source_client[database]
        target_db = target_client[database]

        # Migrate each collection
        collections = ["conversations", "user_states"]
        for collection in collections:
            logger.info(f"Migrating collection: {collection}")

            # Get all documents from source
            docs = list(source_db[collection].find())

            if docs:
                # Insert into target
                target_db[collection].insert_many(docs)
                logger.info(f"Migrated {len(docs)} documents")
            else:
                logger.info("No documents to migrate")

        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
    finally:
        source_client.close()
        target_client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MongoDB Migration Tool")
    parser.add_argument("--source", required=True, help="Source MongoDB URI")
    parser.add_argument("--target", required=True, help="Target MongoDB URI")
    parser.add_argument("--database", required=True, help="Database name")

    args = parser.parse_args()
    migrate_data(args.source, args.target, args.database)
