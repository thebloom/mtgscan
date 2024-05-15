import json
import logging
import re
from functools import partial
from pathlib import Path

import requests
from symspellpy import SymSpell, Verbosity, editdistance

from .box_text import BoxTextList
from .deck import Deck, Pile

URL_ALL_CARDS = "https://mtgjson.com/api/v5/VintageAtomic.json"  # URL to download card list, if needed
URL_KEYWORDS = "https://mtgjson.com/api/v5/Keywords.json"


def load_json(url):
    print(f"Loading {url}")
    r = requests.get(url)
    return r.json()


class MagicRecognition:
    def __init__(self,
                 file_all_cards: str,
                 file_keywords: str,
                 cube_cards: list[str],
                 languages=("English", ),
                 max_ratio_diff=0.5,
                 max_ratio_diff_keyword=0.2) -> None:
        """Load dictionnaries of cards and keywords

        Parameters
        ----------
        file_all_cards: str
            Path to the file containing all cards. If the file does not exist, it is downloaded from mtgjson.
        file_keywords: str
            Path to the file containing all keywords. If the file does not exist, it is downloaded from mtgjson.
        max_ratio_diff : float, optional
            Maximum ratio (distance/length) for a text to be considered as a card name, by default 0.3
        max_ratio_diff_keyword : float, optional
            Maximum ratio (distance/length) for a text to be considered as a (ignored) keyword, by default 0.2
        """
        self.max_ratio_diff = max_ratio_diff
        self.max_ratio_diff_keyword = max_ratio_diff_keyword

        if not Path(file_all_cards).is_file():

            def write_card(f, card):
                i = card.find(" //")
                if i != -1:
                    card = card[:i]
                f.write(card + "$1\n")  # required for SymSpell

            all_cards_json = load_json(URL_ALL_CARDS)
            with Path(file_all_cards).open("a") as f:
                for card, l in all_cards_json["data"].items():
                    if "English" in languages:
                        write_card(f, card)
                    for e in l[0]["foreignData"]:
                        if e["language"] in languages:
                            write_card(f, e["name"])

        self.sym_all_cards = SymSpell(max_dictionary_edit_distance=6)
        self.sym_all_cards._distance_algorithm = editdistance.DistanceAlgorithm.LEVENSHTEIN
        # self.sym_all_cards.load_dictionary(file_all_cards, 0, 1, separator="$")
        
        # define cards in cube
        # cards = ["Giver of Runes","Blade Splicer","Flickerwisp","Monastery Mentor","Recruiter of the Guard","Thalia, Heretic Cathar","Student of Warfare","Porcelain Legionnaire","Mother of Runes","Restoration Angel","Karmic Guide","Hero of Bladehold","Sun Titan","Elesh Norn, Grand Cenobite","Tithe Taker","Leonin Arbiter","Stoneforge Mystic","Path to Exile","Swords to Plowshares","Unexpectedly Absent","Balance","Council's Judgment","Mana Tithe","Lingering Souls","Spectral Procession","Armageddon","Wrath of God","Terminus","Parallax Wave","Thalia, Guardian of Thraben","Leonin Relic-Warder","Delver of Secrets","Baral, Chief of Compliance","Jace, Vryn's Prodigy","Phantasmal Image","Snapcaster Mage","Trinket Mage","True-Name Nemesis","Wall of Omens","Thraben Inspector","Urza, Lord High Artificer","Venser, Shaper Savant","Phyrexian Metamorph","Narset, Parter of Veils","Jace, the Mind Sculptor","Ancestral Recall","Brainstorm","Force Spike","Vendilion Clique","Mystical Tutor","Spell Pierce","Brain Freeze","Counterspell","Daze","Mana Drain","Mana Leak","High Tide","Remand","Frantic Search","Cryptic Command","Fact or Fiction","Turnabout","Force of Will","Mystic Confluence","Memory Lapse","Miscalculation","Gitaxian Probe","Ponder","Preordain","Sleight of Hand","Chart a Course","Merchant Scroll","Time Walk","Show and Tell","Dig Through Time","Tinker","Mind's Desire","Time Spiral","Upheaval","Putrid Imp","Dark Confidant","Oona's Prowler","Vampire Hexmage","Timetwister","Shriekmaw","Grave Titan","Griselbrand","Liliana of the Veil","Dark Ritual","Entomb","Fatal Push","Rain of Filth","Rotting Regisaur","Cabal Ritual","Tainted Pact","Corpse Dance","Dismember","Duress","Inquisition of Kozilek","Reanimate","Thoughtseize","Vampiric Tutor","Demonic Tutor","Exhume","Hymn to Tourach","Night's Whisper","Toxic Deluge","Yawgmoth's Will","Damnation","Tendrils of Agony","Collective Brutality","Animate Dead","Dance of the Dead","Necromancy","Recurring Nightmare","Goblin Guide","Goblin Welder","Grim Lavamancer","Monastery Swiftspear","Mind Twist","Goblin Rabblemaster","Magus of the Moon","Flametongue Kavu","Inferno Titan","Worldgorger Dragon","Chandra, Torch of Defiance","Lightning Bolt","Red Elemental Blast","Young Pyromancer","Ancient Grudge","Seething Song","Through the Breach","Fireblast","Chain Lightning","Faithless Looting","Firebolt","Pyroclasm","Abrade","Wheel of Fortune","Empty the Warrens","Fiery Confluence","Mana Flare","Sulfuric Vortex","Sneak Attack","Arbor Elf","Birds of Paradise","Light Up the Stage","Joraga Treespeaker","Noble Hierarch","Collector Ouphe","Lotus Cobra","Rofellos, Llanowar Emissary","Sakura-Tribe Elder","Scavenging Ooze","Sylvan Caryatid","Elvish Mystic","Wall of Blossoms","Wall of Roots","Eternal Witness","Managorger Hydra","Reclamation Sage","Tireless Tracker","Courser of Kruphix","Oracle of Mul Daya","Tarmogoyf","Primeval Titan","Craterhoof Behemoth","Woodfall Primus","Garruk Wildspeaker","Crop Rotation","Dissenter's Deliverance","Channel","Regrowth","Thragtusk","Natural Order","Scapeshift","Green Sun's Zenith","Fastbond","Oath of Druids","Survival of the Fittest","Sylvan Library","Heartbeat of Spring","Eureka","Spell Queller","Teferi, Time Raveler","Supreme Verdict","Baleful Strix","Thief of Sanity","Daretti, Ingenious Iconoclast","Kolaghan's Command","Manamorphose","Geist of Saint Traft","Knight of the Reliquary","Tidehollow Sculler","Vindicate","Deathrite Shaman","Abrupt Decay","Pernicious Deed","Fire","Dack Fayden","Bloodbraid Elf","Lightning Helix","Leovold, Emissary of Trest","Black Lotus","Chrome Mox","Everflowing Chalice","Lion's Eye Diamond","Lotus Petal","Mana Crypt","Figure of Destiny","Mox Emerald","Mox Jet","Mox Pearl","Mox Ruby","Mox Sapphire","Mana Vault","Pithing Needle","Relic of Progenitus","Mox Diamond","Skullclamp","Sol Ring","Azorius Signet","Boros Signet","Dimir Signet","Golgari Signet","Grim Monolith","Gruul Signet","Sensei's Divining Top","Null Rod","Orzhov Signet","Pentad Prism","Rakdos Signet","Selesnya Signet","Simic Signet","Smuggler's Copter","Sphere of Resistance","Izzet Signet","Umezawa's Jitte","Winter Orb","Basalt Monolith","Coalition Relic","Crucible of Worlds","Tangle Wire","Worn Powerstone","Mystic Forge","Thorn of Amethyst","Memory Jar","Phyrexian Revoker","Scrapheap Scrounger","Metalworker","Lodestone Golem","Solemn Simulacrum","Wurmcoil Engine","Myr Battlesphere","Batterskull","Blightsteel Colossus","Emrakul, the Promised End","Emrakul, the Aeons Torn","Adarkar Wastes","Ancient Tomb","Arid Mesa","Badlands","Bayou","Sundering Titan","Blood Crypt","Bloodstained Mire","Breeding Pool","Brushland","Celestial Colonnade","City of Brass","City of Traitors","Creeping Tar Pit","Bazaar of Baghdad","Flooded Strand","Gaea's Cradle","Godless Shrine","Hallowed Fountain","Karakas","Karplusan Forest","Mana Confluence","Dark Depths","Misty Rainforest","Overgrown Tomb","Plateau","Polluted Delta","Raging Ravine","Sacred Foundry","Savannah","Mishra's Workshop","Marsh Flats","Scrubland","Steam Vents","Stomping Ground","Strip Mine","Sulfurous Springs","Temple Garden","Scalding Tarn","Tropical Island","Tundra","Underground River","Underground Sea","Valakut, the Molten Pinnacle","Verdant Catacombs","Thespian's Stage","Tolarian Academy","Taiga","Wasteland","Watery Grave","Windbrisk Heights","Windswept Heath","Wooded Foothills","Karn, Scion of Urza","Nissa, Who Shakes the World","Dire Fleet Daredevil","Volcanic Island","Time Warp","Prismatic Vista","Seasoned Pyromancer","Wrenn and Six","Skyclave Apparition","Dreadhorde Arcanist","Ramunap Excavator","Dryad of the Ilysian Grove","Force of Negation","Golos, Tireless Pilgrim","Hullbreacher","Opposition Agent","Bloodthirsty Adversary","Fractured Identity","Damn","Archon of Cruelty","Birgi, God of Storytelling","Fallen Shinobi","Elite Spellbinder","Thassa's Oracle","Bolas's Citadel","Dragon's Rage Channeler","Ragavan, Nimble Pilferer","Plague Engineer","Expressive Iteration","Dauthi Voidwalker","Emry, Lurker of the Loch","Prismatic Ending","Usher of the Fallen","Abundant Harvest","Laelia, the Blade Reforged","Augur of Autumn","Esper Sentinel","Fury","Thieving Skydiver","Ignoble Hierarch","Underworld Breach","Urza's Saga","Bloodchief's Thirst","Ravenous Chupacabra","Rampaging Ferocidon","Omnath, Locus of Creation","Niv-Mizzet Reborn","Oko, Thief of Crowns","Luminarch Aspirant","Elvish Reclaimer","Finale of Devastation","Bomat Courier","Fable of the Mirror-Breaker","The Wandering Emperor","Lion Sash","Adeline, Resplendent Cathar","Adanto Vanguard","Walking Ballista","Sedgemoor Witch","Infernal Grasp","Ulamog, the Ceaseless Hunger","Grist, the Hunger Tide","Echo of Eons","Teferi, Hero of Dominaria","Bonecrusher Giant","Murderous Rider","Grief","Unholy Heat","Force of Vigor","Palace Jailer","Wishclaw Talisman","Kaito Shizuki","Shallow Grave","Spellseeker","Glorybringer","Bone Shards","Ketria Triome","Zagoth Triome","Indatha Triome","Savai Triome","Xander's Lounge","Ziatora's Proving Ground","Spara's Headquarters","Raffine's Tower","Raugrin Triome","Tourach, Dread Cantor","Archivist of Oghma","Kaldra Compleat","White Plume Adventurer","Undermountain Adventurer","Caves of Chaos Adventurer","Minsc & Boo, Timeless Heroes","Seasoned Dungeoneer","Jetmir's Garden","The One Ring","Forth Eorlingas!","Orcish Bowmasters","Solitude","Sheoldred, the Apocalypse","Mishra's Bauble","Urza's Bauble","Portal to Phyrexia","Delighted Halfling","Tamiyo, Collector of Tales","Leyline Binding","Intrepid Adversary","Loran of the Third Path","Ephemerate","Reprieve","Ledger Shredder","Chrome Host Seedshark","Zuran Orb","Hard Evidence","Lórien Revealed","Dream Halls","Custodi Lich","Troll of Khazad-dûm","Snuff Out","Atraxa, Grand Unifier","Mine Collapse","Displacer Kitten","Flash","Titania, Protector of Argoth","Palantír of Orthanc","Worldspine Wurm","Nissa, Ascended Animist","Life from the Loam","Yawgmoth, Thran Physician","Kaito, Dancing Shadow","Hexdrinker","Etali, Primal Conqueror","Lurrus of the Dream-Den","Tear Asunder","Sail into the West","Retrofitter Foundry","Kinnan, Bonder Prodigy","The Mightstone and Weakstone","Helm of Awakening","Fire Covenant","Faerie Mastermind","Brazen Borrower","Haywire Mite","Pest Infestation","Exploration","Bloodtithe Harvester","Saheeli, Sublime Artificer","Third Path Iconoclast","Staff of the Storyteller","Knight of Autumn","Goldspan Dragon","Subtlety","Lotus Field","Sheoldred's Edict","Portable Hole","Once Upon a Time","Mox Opal","Currency Converter","Boseiju, Who Endures","Zirda, the Dawnwaker","Coveted Jewel","Kumano Faces Kakkazan","Comet, Stellar Pup","Squee, Dubious Monarch","Rampaging Raptor","Molten Collapse","Otawara, Soaring City","Waterlogged Grove","Fiery Islet","Sunbaked Canyon","Nurturing Peatland","Silent Clearing","The Flux","Graveyard Trespasser","Hangarback Walker","Cathar Commando","Inti, Seneschal of the Sun","Oliphaunt","Archon of Emeria","Voice of Resurgence","Malcolm, Alluring Scoundrel","Bitter Triumph","Questing Beast","Broadside Bombardiers","Shelldock Isle","Aragorn, King of Gondor","Deep-Cavern Bat","Torsten, Founder of Benalia","Sentinel of the Nameless City","Samwise the Stouthearted","Concealing Curtains","Gut, True Soul Zealot","Embereth Shieldbreaker","Cryptic Coat","Forensic Gadgeteer","Get Lost","Shadowy Backstreet","Frost Fair Lure Fish","Lush Portico","Scion of Draco","Tribal Flames","Lazav, Wearer of Faces","Elegant Parlor","Territorial Kavu","Scholar of New Horizons","Novice Inspector","Kappa Cannoneer","Life","Nishoba Brawler","Unruly Krasis","Esika's Chariot","Carnage Interpreter","Pyrokinesis","Flame Slash","Rite of Flame","From the Catacombs","Tishana's Tidebinder","Demonic Consultation","Doomsday","Hedge Maze","March of Otherworldly Light","Sauron's Ransom","Jace, Wielder of Mysteries","Thundering Falls","Underground Mortuary","Containment Priest","Raucous Theater","Preacher of the Schism","Mawloc","Chaos Defiler"]
        # cards = ["Sol Ring", "Lightning Bolt", "Duress", "Island", "Flooded Strand", "Boseiju, Who Shelters All", "Fireblast", "Entomb", "Liliana of the Veil", "Mox Diamond", "Sun Titan", "Empty the Warrens", "Taiga", "tundra", "Scrubland"]
        # add cards in the cube card list to the dictionary one by one
        for card in cube_cards:
            self.sym_all_cards.create_dictionary_entry(card, 1)
        # for testing: print the total number of words, should match number of cards in cube
        print(self.sym_all_cards.word_count)

        self.all_cards = self.sym_all_cards._words
        print(f"Loaded {file_all_cards}: {len(self.all_cards)} cards")
        self.edit_dist = editdistance.EditDistance(editdistance.DistanceAlgorithm.LEVENSHTEIN)

        if not Path(file_keywords).is_file():
            keywords = load_json(URL_KEYWORDS)
            json.dump(keywords, Path(file_keywords).open("w"))

        def concat_lists(LL):
            res = []
            for L in LL:
                res.extend(L)
            return res

        keywords_json = json.load(Path(file_keywords).open())
        keywords = concat_lists(keywords_json["data"].values())
        keywords.extend(["Display", "Land", "Search", "Profile"])
        self.sym_keywords = SymSpell(max_dictionary_edit_distance=3)
        for k in keywords:
            self.sym_keywords.create_dictionary_entry(k, 1)
        print(f"Loaded {file_keywords}: {len(keywords)} keywords")

    def _preprocess(self, text: str) -> str:
        """Remove characters which can't appear on a Magic card (OCR error)"""
        return re.sub("[^a-zA-Z',. ]", '', text).rstrip(' ')

    def _preprocess_texts(self, box_texts: BoxTextList) -> None:
        """Apply `preprocess` on each text"""
        for box_text in box_texts:
            box_text.text = self._preprocess(box_text.text)

    def box_texts_to_cards(self, box_texts: BoxTextList) -> BoxTextList:
        """Recognize cards from raw texts"""
        box_texts.sort()
        box_cards = BoxTextList()
        for box, text, _ in box_texts:
            sug = self.sym_keywords.lookup(text,
                                           Verbosity.CLOSEST,
                                           max_edit_distance=min(3, int(self.max_ratio_diff_keyword * len(text))))
            if sug != []:
                logging.info(f"Keyword rejected: {text} {sug[0].distance/len(text)} {sug[0].term}")
            else:
                card = self._search(self._preprocess(text))
                if card is not None:
                    box_cards.add(box, card)
        return box_cards

    def _assign_stacked(self, box_texts: BoxTextList, box_cards: BoxTextList) -> None:
        """Set multipliers (e.g. x4) for each (stacked) card in `box_cards`

        Parameters
        ----------
        box_texts : BoxTextList
            BoxTextList containing potential multipliers
        box_cards : BoxTextList
            BoxTextList containing recognized cards
        """
        def _assign_stacked_one(box_cards: BoxTextList, m: int, comp) -> None:
            i_min = 0
            for i, box_card in enumerate(box_cards):
                if comp(box_card.box, box_cards[i_min].box):
                    i_min = i
            box_cards[i_min].n = m
            logging.info(f"{box_cards[i_min].text} assigned to x{m}")

        def dist(p: tuple, q: tuple) -> float:
            return (p[0] - q[0])**2 + (p[1] - q[1])**2

        def comp_md(box1: tuple, box2: tuple, box: tuple) -> float:
            if box1[0] > box[0] or box1[1] > box[1]:
                return False
            return dist(box, box1) < dist(box, box2)

        def comp_sb(box1: tuple, box2: tuple, box: tuple) -> float:
            return dist(box, box1) < dist(box, box2)

        comp = (comp_md, comp_sb)
        for box, text, _ in box_texts:
            if len(text) == 2:
                for i in [0, 1]:
                    if text[i] in '×xX' and text[1 - i].isnumeric():
                        _assign_stacked_one(box_cards, int(text[1 - i]), partial(comp[i], box=box))

    def _box_cards_to_deck(self, box_cards: BoxTextList) -> Deck:
        """Convert recognized cards to decklist"""
        maindeck, sideboard = Pile(), Pile()
        n_cards = sum(c.n for c in box_cards)
        n_added = 0
        last_main_card = max(60, n_cards - 15)
        for _, card, n in box_cards:

            def add_cards(c, deck, p):
                if c in deck.cards:
                    deck.cards[c] += p
                elif p > 0:
                    deck.cards[c] = p

            n_added_main = max(min(n, last_main_card - n_added), 0)
            add_cards(card, maindeck, n_added_main)
            add_cards(card, sideboard, n - n_added_main)
            n_added += n
        deck = Deck()
        deck.maindeck = maindeck
        deck.sideboard = sideboard
        return deck

    def box_texts_to_deck(self, box_texts: BoxTextList) -> Deck:
        """Convert raw texts to decklist

        Parameters
        ----------
        box_texts : BoxTextList
            Raw texts given by an OCR

        Returns
        -------
        Deck
            Decklist obtained from `box_texts`
        """
        box_cards = self.box_texts_to_cards(box_texts)
        self._assign_stacked(box_texts, box_cards)
        return self._box_cards_to_deck(box_cards)

    def _search(self, text):
        """If `text` can be recognized as a Magic card, return that card. Otherwise, return None."""
        if len(text) < 3:  # a card name is never that short
            return None
        if len(text) > 30:  # a card name is never that long
            logging.info(f"Too long: {text}")
            return None
        if text in self.all_cards:
            return text
        i = text.find("..")  # search for truncated card name
        if i != -1:
            dist = int(self.max_ratio_diff * i)
            card = None
            t = text[:i]
            for c in self.all_cards:
                d = self.edit_dist.compare(text[:i], c[:i], dist)
                if d != -1 and d < dist:
                    card = c
                    dist = d
            if card is None:
                logging.info(f"Not prefix: {text}")
            else:
                logging.info(f"Found prefix: {text} {dist/i} {card}")
                return card
        else:
            text = text.replace('.', '').rstrip(' ')
            sug = self.sym_all_cards.lookup(text,
                                            Verbosity.CLOSEST,
                                            max_edit_distance=min(6, int(self.max_ratio_diff * len(text))))
            if sug != []:
                card = sug[0].term
                ratio = sug[0].distance / len(text)
                if len(text) < len(card) + 7:
                    logging.info(f"Corrected: {text} {ratio} {card}")
                    return card
                logging.info(f"Not corrected (too long): {text} {ratio} {card}")
            else:
                logging.info(f"Not found: {text}")
        return None
