class FontInfo:

    def __init__ (self, name, type, encoding, emb, sub, uni, obj, id):
        if '+' in name:
            self.name = name[name.find('+')+1:]
        else:
            self.name = name
        self.type = type
        self.encoding = encoding
        self.emb = emb
        self.sub = sub
        self.uni = uni
        self.object = obj
        self.id = id
