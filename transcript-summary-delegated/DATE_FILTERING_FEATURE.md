# Date Range Filtering Feature

## Overview

The app now supports filtering meetings by date range. Users can select a start date and end date on the home page to retrieve only meetings within that timeframe.

---

## What Was Added

### 1. ✅ Frontend Changes (`templates/home.html`)

#### Date Range Inputs
Added date picker inputs in the form:

```html
<div class="form-row">
    <div class="form-group">
        <label for="start_date">Start Date:</label>
        <input type="date" id="start_date" name="start_date" required>
    </div>
    
    <div class="form-group">
        <label for="end_date">End Date:</label>
        <input type="date" id="end_date" name="end_date" required>
    </div>
</div>
```

#### Default Date Range
Automatically sets default dates to last 30 days:

```javascript
function setDefaultDates() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('end_date').valueAsDate = endDate;
    document.getElementById('start_date').valueAsDate = startDate;
}
```

#### Date Validation
Validates date range before submitting:

```javascript
function getDateRange() {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    
    if (!startDate || !endDate) {
        showError('Please select both start and end dates');
        return null;
    }
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (start > end) {
        showError('Start date must be before end date');
        return null;
    }
    
    return { start_date: startDate, end_date: endDate };
}
```

### 2. ✅ Styling (`static/style.css`)

Added responsive grid layout for date inputs:

```css
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 25px;
}

@media (max-width: 768px) {
    .form-row {
        grid-template-columns: 1fr;
    }
}

.form-group input[type="date"] {
    width: 100%;
    padding: 12px 15px;
    border: 2px solid #e0e0e0;
    border-radius: 5px;
    font-size: 1rem;
    transition: border-color 0.3s;
}
```

### 3. ✅ Backend Changes

#### Updated `app.py`

**Zoom Endpoint:**
```python
@app.route('/list/zoom/meetings', methods=['POST'])
def list_zoom_meetings():
    data = request.get_json()
    email = data.get('email')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    recordings = zoom_service.list_recordings(email, start_date, end_date)
    # ...
```

**Teams Endpoint:**
```python
@app.route('/list/teams/meetings', methods=['POST'])
def list_teams_meetings():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    meetings = graph_service.list_meetings(access_token, start_date, end_date)
    # ...
```

#### Updated `services/zoom_service.py`

```python
def list_recordings(self, email, start_date=None, end_date=None):
    """
    Get list of recorded meetings for a user
    
    Args:
        email: User's email address
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    if self.use_mock:
        # Filter mock data by date
        recordings = self.mock_recordings.get(user_id, [])
        if start_date and end_date:
            # Date filtering logic for mock data
            # ...
    else:
        # Add date parameters to Zoom API call
        endpoint = f"/v2/users/{user_id}/recordings"
        if start_date:
            endpoint += f"?from={start_date}&to={end_date}"
        # ...
```

#### Updated `services/graph_service.py`

```python
def list_meetings(self, access_token, start_date=None, end_date=None):
    """
    Get list of recorded Teams meetings for the authenticated user
    
    Args:
        access_token: User's access token
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    if self.use_mock:
        # Filter mock data by date
        # ...
    else:
        # Build OData filter with date range
        filters = ["recordingStatus eq 'available'"]
        if start_date and end_date:
            filters.append(f"startDateTime ge '{start_date}T00:00:00Z'")
            filters.append(f"startDateTime le '{end_date}T23:59:59Z'")
        # ...
```

---

## How It Works

### User Flow

```
1. User visits home page
   ↓
2. Form pre-filled with:
   - Start Date: 30 days ago
   - End Date: Today
   ↓
3. User can adjust dates or keep defaults
   ↓
4. User enters email (for Zoom) or is authenticated (for Teams)
   ↓
5. Clicks "Get Zoom Meetings" or "Get Teams Meetings"
   ↓
6. JavaScript validates:
   - Both dates are selected ✓
   - Start date ≤ End date ✓
   ↓
7. AJAX request sent with:
   { email, start_date, end_date }
   ↓
8. Backend validates dates
   ↓
9. Service layer filters meetings by date:
   - Mock mode: Client-side filtering
   - Real API: Server-side filtering (via API params)
   ↓
10. Only meetings within date range returned
```

---

## Date Format

### Frontend → Backend
- **Format**: `YYYY-MM-DD` (ISO 8601 date)
- **Example**: `2025-01-01`
- **Source**: HTML5 `<input type="date">` value

### Backend → Services
- **Zoom API**: `from=YYYY-MM-DD&to=YYYY-MM-DD`
- **Graph API**: OData filter with ISO 8601 datetime
  - `startDateTime ge '2025-01-01T00:00:00Z'`
  - `startDateTime le '2025-01-31T23:59:59Z'`

### Mock Data Filtering
- Parses ISO datetime strings from mock data
- Compares with date range
- Returns filtered results

---

## API Examples

### Zoom API Call (Real)
```
GET /v2/users/{userId}/recordings?from=2025-01-01&to=2025-01-31
Authorization: Bearer {access_token}
```

### Graph API Call (Real)
```
GET /me/onlineMeetings?$filter=recordingStatus eq 'available' 
    and startDateTime ge '2025-01-01T00:00:00Z' 
    and startDateTime le '2025-01-31T23:59:59Z'
    &$top=50
Authorization: Bearer {access_token}
```

---

## Testing

### With Mock Data (Default)

1. Start app: `python app.py`
2. Visit: `http://localhost:5001`
3. Notice default dates (last 30 days)
4. Change dates to narrow range (e.g., last week)
5. Click "Get Zoom Meetings" or "Get Teams Meetings"
6. See filtered mock meetings

### With Real APIs

1. Set `USE_MOCK_DATA=false` in `.env`
2. Configure Azure/Zoom credentials
3. Test date filtering:
   - Try last 7 days
   - Try last 30 days
   - Try last 90 days
   - Try custom range

### Edge Cases to Test

| Test Case | Expected Result |
|-----------|----------------|
| **Start date > End date** | Error: "Start date must be before end date" |
| **No dates selected** | Error: "Please select both start and end dates" |
| **Very old date range** | Returns empty list (no meetings) |
| **Future date range** | Returns empty list (no meetings yet) |
| **Today only (same start/end)** | Returns today's meetings only |
| **Large range (1+ years)** | May hit API limits, returns available meetings |

---

## Benefits

### User Experience
✅ **Default convenience**: Last 30 days pre-selected  
✅ **Flexibility**: Can customize any date range  
✅ **Validation**: Prevents invalid date ranges  
✅ **Responsive**: Mobile-friendly date pickers  

### Performance
✅ **Reduced data**: Only fetches relevant meetings  
✅ **Faster loading**: Smaller result sets  
✅ **API efficiency**: Uses native API filtering (not client-side)  

### Compliance
✅ **Data minimization**: Only retrieves necessary data  
✅ **API quotas**: Reduces unnecessary API calls  

---

## Customization

### Change Default Date Range

Edit `templates/home.html`:

```javascript
function setDefaultDates() {
    const endDate = new Date();
    const startDate = new Date();
    
    // Change this number for different default range
    startDate.setDate(startDate.getDate() - 7);  // Last 7 days
    // OR
    startDate.setDate(startDate.getDate() - 90);  // Last 90 days
    
    document.getElementById('end_date').valueAsDate = endDate;
    document.getElementById('start_date').valueAsDate = startDate;
}
```

### Add Date Range Presets

Add quick select buttons:

```html
<div class="date-presets">
    <button type="button" onclick="setDateRange(7)">Last 7 Days</button>
    <button type="button" onclick="setDateRange(30)">Last 30 Days</button>
    <button type="button" onclick="setDateRange(90)">Last 90 Days</button>
</div>
```

```javascript
function setDateRange(days) {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    document.getElementById('end_date').valueAsDate = endDate;
    document.getElementById('start_date').valueAsDate = startDate;
}
```

---

## Troubleshooting

### Dates Not Filtering (Mock Mode)

**Check:**
1. Console logs in `zoom_service.py` / `graph_service.py`
2. Verify mock data has valid `start_time` fields
3. Ensure date parsing logic handles your mock data format

### Dates Not Filtering (Real API)

**Zoom:**
- Zoom API requires `from` and `to` parameters
- Date format must be `YYYY-MM-DD`
- Check Zoom API documentation for any changes

**Teams (Graph API):**
- OData filter syntax is strict
- Datetime must include timezone (`Z` for UTC)
- Check Graph API logs for filter errors

### Invalid Date Error

**Common causes:**
- Browser doesn't support `<input type="date">`
- Date format mismatch
- Timezone conversion issues

**Solution:**
- Use a date picker library (e.g., flatpickr) for older browsers
- Always use ISO 8601 format
- Handle timezones explicitly

---

## Future Enhancements

### Potential Improvements

1. **Date Range Validation**
   - Limit max range (e.g., 1 year max)
   - Warn if range is too large

2. **Saved Preferences**
   - Remember user's last date range
   - Store in localStorage or user profile

3. **Calendar View**
   - Visual calendar picker
   - Show days with meetings highlighted

4. **Quick Filters**
   - "This Week", "This Month", "This Quarter"
   - "Last Meeting", "Upcoming Meetings"

5. **Time Zone Support**
   - Allow user to select timezone
   - Convert all times to user's local timezone

---

## Summary

✅ **Feature Complete**: Date filtering working for both Zoom and Teams  
✅ **User Friendly**: Default range (last 30 days) pre-selected  
✅ **Validated**: Client-side and server-side validation  
✅ **Responsive**: Mobile-friendly design  
✅ **Efficient**: Uses native API filtering  

**Ready to use!** 🎉

The date filtering feature is fully functional and integrated throughout the application. Users can now easily filter meetings by selecting their desired date range.

