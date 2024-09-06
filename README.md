# Markovify

This is a fork of Markovify meant for internal use. Consumes almost no memory when training and generating sentences, in the name of slightly lower overall performance and a way smaller feature set. This fork also has no external dependencies.

```py
# Train
Input(input_path="data/output.txt",
      output_path="data/text_model.db", state_size=2)

# Output
text_model = Output("data/text_model.db")
sentence = text_model.make_sentence()
```

For faster training, you might want to install [GNU dbm](https://www.gnu.org.ua/software/gdbm/).
