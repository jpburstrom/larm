data = [0, 1, 0, 1, 1, 0, 1]
def test(data):
    for i in data:
        data = data[1:]
        yield data

for k in test(data):
    print k

