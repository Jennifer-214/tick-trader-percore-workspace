---
type: concurrency-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.8 (DEFERRED INDEFINITELY)
sister_specs:
  - concurrency-patterns/dpdk-userspace-networking-pattern.md (parent; DPDK context)
  - concurrency-patterns/ktls-kernel-tls-pattern.md (sister; kernel-side analog)
tags: [concurrency, userspace-tls, dpdk, encryption, aes-gcm]
surface: [tls-encryption, dpdk]
---

# Userspace TLS pattern (Stage 2 DRAFT — DEFERRED)

**Pattern intent:** TLS 1.3 + AES-GCM encryption in userspace (no kernel; required when using DPDK since kernel-bypass means kTLS unavailable). DEFERRED per D-57.

## Pattern outline

```cpp
struct UserspaceTLSState {
    enum { HANDSHAKE_INIT, HANDSHAKE_DONE, ESTABLISHED } state;

    // Session keys (post-handshake)
    uint8_t client_write_key[32];
    uint8_t server_read_key[32];
    uint8_t client_iv[12];
    uint8_t server_iv[12];

    // Record sequence numbers
    uint64_t client_seq;
    uint64_t server_seq;
};

int UserspaceTLS_EncryptRecord(UserspaceTLSState* tls,
                                const void* plaintext, size_t plain_len,
                                void* ciphertext, size_t* cipher_len) {
    uint8_t nonce[12];
    memcpy(nonce, tls->client_iv, 12);
    *(uint64_t*)(nonce + 4) ^= htobe64(tls->client_seq);

    // Use hardware AES-NI (~1-3μs per record)
    AES_GCM_Encrypt(tls->client_write_key, nonce, plaintext, plain_len, ciphertext);

    tls->client_seq++;
    return 0;
}
```

## Mitigation: hand-rolled crypto is risky

Recommendation: use OpenSSL with custom BIO that goes to DPDK rings. OpenSSL handles the TLS state machine + crypto; we just provide the BIO transport layer. Reduces hand-rolled crypto risk.

## Stage progression

- **Stage 2 DRAFT**: reference; awaits DPDK hardware
- **Stage 3 first canonical**: with DPDK deployment

## Cross-references

- Parent: `concurrency-patterns/dpdk-userspace-networking-pattern.md`
- Sister: `concurrency-patterns/ktls-kernel-tls-pattern.md`
