let $ = require('jquery')
let env = require('./env')
let util = require('./util')
let log = util.log
let isInt = util.isInt

let logText = $('#log-text')

function updateLogFileList () {
  let logFilesListHTML = []
  $.getJSON('logs', res =>{
    $.each(res.files, (key, value) =>{
      logFilesListHTML += `<li><a onClick="window.switchToLog(${ value[0] +1 })"
        id="log-${ value[0] }">${ value[1] }</a></li>` })
    $('#log-files').html(logFilesListHTML)
    
    // todo: better highlighting, focus is ephemeral
    //$('#log-' + env.shownLog.id).focus()
  })
}

function getSetState (state) {
  state = state || {}
  let anchor = util.parseAnchor()
  anchor = {
    log:      state.log     ||  anchor.log      || 1,
    offset:   state.offset  ||  anchor.offset   || 1 }
  document.location.hash = 
    `#log:${ anchor.log };offset:${ anchor.offset }`
  return anchor
}

function updatePathAndStatus (state) {
  if (state.log === env.lastLogID) ;
  else $.getJSON('logs/' + (+state.log -1), function (res) {
    $('#log-path').html('<!-- js generated --><span class="glyphicon glyphicon-' 
      + env.icon[res.status][0]
      + '" aria-hidden="true" style="font-size: 34px; color: ' + env.icon[res.status][1]
      + '; width: 42px; margin-right: 4px; vertical-align: middle;"></span>'
      + '<input class="form-control" type="text" value="' + res.filename
      + '" readonly onClick="this.select();"><!-- /js generated -->' ) })
}

function insertLogData (linesArray) {
  let [html, lineStatus] = [``, ``] 
  linesArray.forEach((val, index) =>{
    lineStatus = env.logLine[val[0]]
    html = lineStatus ? `<mark class="${ env.logLine[val[0]][0] }"
      style="background-color: ${ env.logLine[val[0]][1] };">` : ``
    html += val[1] + '\n'
    html += lineStatus ? `</mark>` : ``
    logText.append(html) })
}

function clearLog () { logText.html('') }

let fadeLog = {
  out: x =>{
    setTimeout(clearLog, env.transitionTime * 0.5)
    logText.fadeOut(env.transitionTime * 0.5) },
  in: x =>{ logText.fadeIn(env.transitionTime * 0.5) }
}

function displayLogSection (state, availableLines) {
  let url = `logs/${ state.log -1 }/${ state.offset -1 }:${ availableLines }:1`
  $.get(url, res =>{
    if (state.log === env.lastLogID) {
      clearLog()
      insertLogData(res.lines) }
    else {
      env.lastLogID = state.log
      fadeLog.out()
      setTimeout(x =>{
        insertLogData(res.lines)
        fadeLog.in()
      }, env.transitionTime * 0.5) }
  })
}

function render (availableLines) {
  availableLines = availableLines || util.determineLineCount()
  let state = getSetState()
  updatePathAndStatus(state)
  displayLogSection(state, availableLines)
}

function switchToLog (id) {
  getSetState({ log: id, offset: 1 })
  render()
}

function getNextOffset (state, direction, availableLines, callback) {
  let url = `logs/${ state.log -1 }/${ state.offset -1 }`
    + `:${ availableLines }:${ direction }`
  $.get(url, res =>{ callback(state, res, availableLines) })
}

function switchPage (direction) {
  var availableLines = util.determineLineCount()
  getNextOffset(getSetState(), direction, availableLines,
    (state, res, availableLines) =>{
      getSetState({ log: state.log, offset: res.offset +1 })
      render(availableLines) })
}

function nextPage () { switchPage(1) }
function previousPage () { switchPage(-1) }

module.exports = {
  render: render,
  switchToLog: switchToLog,
  nextPage: nextPage,
  previousPage: previousPage,
  updateLogFileList: updateLogFileList
}
