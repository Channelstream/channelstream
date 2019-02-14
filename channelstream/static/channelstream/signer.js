import {jsSHA1 as jsSHA} from "./sha1-esm.js";

export class ChannelStreamSigner {

    constructor(secret) {
        this.secret = secret
    }

    intToBytes(x) {
        var bytes = [];
        while (x > 0) {
            bytes.push(String.fromCharCode(x & 255));
            x = x >> 8;
        }
        return btoa(bytes.reverse().join(''));
    }

    hashStrip(input) {
        return input.replace('=', '').replace('+', '-').replace('/', '_');
    }

    signRequest() {
        var salt = 'itsdangerous.Signer';
        var derived_key = salt + 'signer' + this.secret;
        var sep = '.';
        var shaObj = new jsSHA("SHA-1", "TEXT");
        shaObj.update(derived_key)
        derived_key = shaObj.getHash("BYTES");
        var timestamp = Math.floor(Date.now() / 1000);
        var value = 'channelstream' + sep + this.hashStrip(this.intToBytes(timestamp));
        var shaObj = new jsSHA("SHA-1", "TEXT");
        shaObj.setHMACKey(derived_key, "BYTES");
        shaObj.update(value);
        var hmac = shaObj.getHMAC("B64");
        return value + sep + this.hashStrip(hmac);
    }
}

