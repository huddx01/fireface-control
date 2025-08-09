
module.exports = {
    init: ()=>{
        send(...settings.read('send')[0].split(':'), '/server-ready')
    }
}
