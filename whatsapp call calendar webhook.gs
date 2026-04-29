function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents || "{}");

    var calendarName = body.calendarName || "WhatsApp Calls";
    var contact = body.contact || "Unknown";
    var start = body.start ? new Date(body.start) : null;
    var end = body.end ? new Date(body.end) : null;
    var durationSeconds = Number(body.durationSeconds || 0);
    var direction = body.direction || "unknown";
    var source = body.source || "android";

    if (!start && end && durationSeconds > 0) {
      start = new Date(end.getTime() - durationSeconds * 1000);
    }

    if (!end && start && durationSeconds > 0) {
      end = new Date(start.getTime() + durationSeconds * 1000);
    }

    if (!start || !end || isNaN(start.getTime()) || isNaN(end.getTime())) {
      return jsonResponse({
        ok: false,
        error: "Missing or invalid start/end time"
      });
    }

    var calendar = getOrCreateCalendar_(calendarName);
    var title = "WhatsApp call: " + contact;
    var description = [
      "direction: " + direction,
      "durationSeconds: " + durationSeconds,
      "source: " + source
    ].join("\n");

    var event = calendar.createEvent(title, start, end, {
      description: description
    });

    return jsonResponse({
      ok: true,
      eventId: event.getId(),
      title: title
    });
  } catch (err) {
    return jsonResponse({
      ok: false,
      error: String(err)
    });
  }
}

function jsonResponse(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function getOrCreateCalendar_(name) {
  var calendars = CalendarApp.getCalendarsByName(name);
  if (calendars && calendars.length > 0) {
    return calendars[0];
  }
  return CalendarApp.createCalendar(name);
}
