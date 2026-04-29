from openai import OpenAI
from pydantic import BaseModel
from config.config import OPENAI_TOKEN

client = OpenAI(api_key=OPENAI_TOKEN)


class Country(BaseModel):
    country_name: str


def get_country(text: str) -> str | None:
    print("Getting contry via LLM")
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {"role": "system", "content": "Extract the country name from the text"},
            {
                "role": "user",
                "content": text,
            },
        ],
        text_format=Country,
    )
    country_parsed = response.output_parsed
    return country_parsed.country_name if country_parsed else None
