var clients = {},
    [mentat_host, mentat_port] = settings.read('send')[0].split(':')

app.on('open', (data, client)=>{
    clients[client.id] = true
    send(mentat_host, mentat_port, '/gui-clients', Object.values(clients).length)
})

app.on('close', (data, client)=>{
    delete clients[client.id]
    send(mentat_host, mentat_port, '/gui-clients', Object.values(clients).length)
})

module.exports = {

    oscOutFilter: (data)=>{
        var {address, args, host, port, clientId} = data

        // manual client sync (default sync disabled to prevent state sync on connection)
        for (var id in clients) {
            if (id !== clientId) receive(host, port, address, ...args, {clientId: id})
        }

        return data
    },

    init: ()=>{
        send(mentat_host, mentat_port, '/server-ready')
    }

}
