"""Manual ingestion trigger script."""
import asyncio
from app.services.ingestion.pipeline import run_all_sources


async def main():
    result = await run_all_sources()
    print(f"Ingestion complete: {result}")


if __name__ == "__main__":
    asyncio.run(main())
