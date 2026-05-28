---
type: concurrency-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.4
canonical_applications:
  - v5.15.5.F.4d.1.E.4 (kTLS for kernel-side TLS encryption)
sister_specs:
  - concurrency-patterns/io-uring-kernel-bypass-pattern.md (sister; kernel-side I/O)
tags: [concurrency, ktls, kernel-tls, aes-gcm, encryption-offload]
surface: [tls-encryption, kernel-bypass-lite]
---

# kTLS kernel TLS pattern

**Pattern intent:** Offload TLS encryption to kernel via `TLS_TX` + `TLS_RX` socket options. Send/recv plaintext from userspace; kernel encrypts/decrypts. Saves ~5-7μs per record (vs userspace SSL_write).

## Pattern

```cpp
int KTLS_Enable(int socket_fd, SSL* ssl_state) {
    // Require TLS 1.3
    if (SSL_version(ssl_state) != TLS1_3_VERSION) return -1;

    // Verify cipher (AES_GCM_128/256 or CHACHA20_POLY1305)
    const SSL_CIPHER* cipher = SSL_get_current_cipher(ssl_state);
    int cipher_nid = SSL_CIPHER_get_cipher_nid(cipher);
    if (cipher_nid != NID_aes_128_gcm &&
        cipher_nid != NID_aes_256_gcm &&
        cipher_nid != NID_chacha20_poly1305) {
        return -1;
    }

    // Enable TLS upper-layer
    setsockopt(socket_fd, SOL_TCP, TCP_ULP, "tls", 4);

    // Set TX crypto info (encrypt outgoing)
    struct tls12_crypto_info_aes_gcm_128 crypto_tx;
    crypto_tx.info.version = TLS_1_3_VERSION;
    crypto_tx.info.cipher_type = TLS_CIPHER_AES_GCM_128;
    PopulateCryptoInfoFromSSL(&crypto_tx, ssl_state, /*is_tx=*/1);
    setsockopt(socket_fd, SOL_TLS, TLS_TX, &crypto_tx, sizeof(crypto_tx));

    // Set RX crypto info (decrypt incoming)
    struct tls12_crypto_info_aes_gcm_128 crypto_rx;
    crypto_rx.info.version = TLS_1_3_VERSION;
    crypto_rx.info.cipher_type = TLS_CIPHER_AES_GCM_128;
    PopulateCryptoInfoFromSSL(&crypto_rx, ssl_state, /*is_tx=*/0);
    setsockopt(socket_fd, SOL_TLS, TLS_RX, &crypto_rx, sizeof(crypto_rx));

    return 0;
}
```

After kTLS enabled:
- `send(fd, plaintext, len, 0)` → kernel encrypts → ciphertext on wire
- `recv(fd, buf, len, 0)` → ciphertext from wire → kernel decrypts → plaintext

io_uring works on kTLS sockets transparently.

## Kernel requirements

- Linux 5.10+ recommended (TLS 1.3 + ChaCha20 support)
- kTLS module loaded: `modprobe tls`
- Kernel features: `CONFIG_TLS=y`

## Fallback path

If kTLS unavailable:
- cfg flag `ktls_required = false` (default)
- Engine falls back to userspace TLS (SSL_write); ~5-7μs slower per record
- Log warning at boot

If `ktls_required = true` and unavailable: engine refuses to start.

## Cross-references

- Sister: `concurrency-patterns/io-uring-kernel-bypass-pattern.md`
- First application: `plans/v5.15.5.F.4d.1.E.4-io-uring-ktls.md`
