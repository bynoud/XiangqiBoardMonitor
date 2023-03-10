def get_fen(self):
    # Start for highest rank
    fens = []
    rotate = self.mySide==Side.Black
    def addfen(fen, sym):
        spaceSym = f'{"" if spacecnt==0 else spacecnt}'
        if rotate:
            fen = sym + spaceSym + fen
            if sym=='':
                fens.insert(0,fen)
        else:
            fen = fen + spaceSym + sym
            if sym=='':
                fens.append(fen)
        return fen
    for row in range(GRID_HEIGHT): # we save highest rank at 0
        fen = ''
        spacecnt = 0
        for col in range(GRID_WIDTH):
            p = self.positions[row][col]
            if p == '.':
                spacecnt += 1
            else:
                fen = addfen(fen, p)
                spacecnt = 0
        fen = addfen(fen, '')
    return f'{"/".join(fens)}'