from rag_worker import process_file

# def worker():
#     print("Worker started and listening for messages...")
#     while True:
#         # Simulate receiving a message (replace with actual message queue logic)
#         message = receive_message()
#         if message:
#             print(f"Received message: {message}")
#             process_file(message)


def worker(messages):
    print("Worker started and listening for messages...")
    for message in messages:
        print(f"Received message: {message}")
        process_file(message)
    


testData = [{
                "id": 5,
                "file": "Rich Dad Poor Dad.docx",
                "status": "Uploaded",
                "s3_url": "1/1/12d15194-d3d8-4f71-9632-92931a859a37_Rich Dad Poor Dad.docx"
            },
            {
                "id": 6,
                "file": "GenAI.pdf",
                "status": "Uploaded",
                "s3_url": "1/1/66d5f62d-d0ce-442b-9bd9-627cc71bb581_GenAI.pdf"
            }
        ]