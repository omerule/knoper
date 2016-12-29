BEGIN {
	#Print per dir de ACL format = DIR:ACL:SID:[RIGHTS]
	#OutFieldSeparator
	OFS=":"
	#RecordSeparator krijgt hij vanuit het bashscript
	#Deze moet nog wel even goed uitgewerkt liefst met een "^/..." 
	RS="here the mountpoint /mnt/.."
	#FieldSeparator
	FS="\n";
}
{
	#om de lijst goed te Printen zie boven #Print...
	#eerst de DIR vastzetten
	dir= "\"" $1 "\""
	#Records vanaf boven tot aan nieuwe DIR 
	#Print DIR:ACL:SID:[RIGHTS]
	for (i = 2; i < NF; i++)
		if ($i ~ /^ACL/) 
#|| $i ~ /^OWNER/ || $i ~ /^GROUP/)
			print dir ":" $i
		else if ($i ~ /^OWNER/)
			print dir ":" $i ":OWNER"
		else if ($i ~ /^GROUP/)
			print dir ":" $i ":GROUP"
}
