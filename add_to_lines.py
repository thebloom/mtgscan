with open('powercube_cards.txt', 'r') as istr:
    with open('powercube_cards.txt', 'w') as ostr:
        for line in istr:
            line = line.rstrip('\n') + '$1'
            print(line, file=ostr)