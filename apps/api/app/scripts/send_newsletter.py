"""Newsletter send script."""
import asyncio
import argparse


async def main(profile: str, frequency: str):
    from app.services.email.sender import send_newsletter_batch
    await send_newsletter_batch(profile=profile, frequency=frequency)
    print(f"Newsletter {profile}/{frequency} sent.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["investor", "founder", "general"], default="general")
    parser.add_argument("--frequency", choices=["daily", "weekly"], default="weekly")
    args = parser.parse_args()
    asyncio.run(main(args.profile, args.frequency))
