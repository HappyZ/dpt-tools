all: fw.pkg

fw.pkg: base.pkg payload.tar.gz
	echo 12836160f229d466bf4f051ba26fb46697bfa748e81b279b69ad9a5bd340958e $< | openssl sha256 -c
	cp $< $@
	echo "55  -none  -in /tmp/anim_sig.dat" | dd bs=8 count=4 seek=67 of=$@ conv=notrunc
	echo "00 00 00 00" | xxd -r -p >> $@
	echo "00 00 00 00" | xxd -r -p >> $@
	printf '%08x' $$(wc -c < payload.tar.gz) | sed -E 's/(..)(..)(..)(..)/\4\3\2\1/' | xxd -r -p | head -c 4 >> fw.pkg
	cat payload.tar.gz >> $@


payload.tar.gz: FwUpdater
	[ -x $</eufwupdater.sh ]
	tar -cvz --exclude=".*"  --numeric-owner  -f $@ $<

.PHONY: all check_sig payload.tar.gz 

clean:
	-rm fw.pkg payload.tar.gz
