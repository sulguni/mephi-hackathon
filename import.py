import sqlite3
con = sqlite3.connect("db.db", autocommit=True)
f = open("мрази.txt")
for l in f:
    fio, group, gavr, fmba, sum, lastgavr, lastfmba, contacts, phone = l.split("|")
    con.cursor().execute(f"INSERT INTO Donors (Name, GroupID, Gavrilova, FMBA, LastGavrilov, LastFMBA, Contacts, Phone, Stranger) values ({','.join('?' * 9)})", (fio, group, int(gavr) if gavr != "" else 0, int(fmba) if fmba != "" else 0, lastgavr, lastfmba, contacts, phone, int(group != "")))
con.close()
