from app import create_app, db
from app.models import User, Subject, Topic, Subtopic, MockTest, TopicPDF, SubtopicPDF
import os

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Subject=Subject, Topic=Topic,
                Subtopic=Subtopic, MockTest=MockTest)

if __name__ == '__main__':
    port = int(os.environ.get("PORT",5000))
    app.run(debug=True, host="0.0.0.0", port=port)