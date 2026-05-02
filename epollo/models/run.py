from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model='gpt-4.1-mini',
    input='Why is the sky blue?'
)
print(response.output_text)
