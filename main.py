from octorag import OctoRAG


def main():
    model = OctoRAG()

    while True:
        query = input('Enter query. Enter "quit" to quit.\n')
        if query.lower() == "quit":
            break

        print(model.query(query))
