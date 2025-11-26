# Human Feedback Loop System

**The Good Shepherd** includes a comprehensive feedback system that allows analysts to provide input on event quality, relevance, and accuracy. This feedback is used to continuously improve LLM enrichment algorithms and event scoring.

## Overview

The feedback system enables:
- **Quality Improvement**: Refine LLM enrichment accuracy over time
- **Relevance Tuning**: Better understand what events matter to users
- **False Positive Detection**: Identify and filter out irrelevant events
- **Category Refinement**: Improve automatic categorization accuracy

## Feedback Types

### 1. Accuracy Rating

Rate the overall accuracy of the event enrichment (1-5 stars):

- ⭐ **1 Star**: Completely inaccurate, wrong information
- ⭐⭐ **2 Stars**: Mostly inaccurate, significant errors
- ⭐⭐⭐ **3 Stars**: Partially accurate, some errors
- ⭐⭐⭐⭐ **4 Stars**: Mostly accurate, minor issues
- ⭐⭐⭐⭐⭐ **5 Stars**: Completely accurate, excellent enrichment

### 2. Relevance Rating

Rate how relevant the event is to your mission (1-5 stars):

- ⭐ **1 Star**: Completely irrelevant
- ⭐⭐ **2 Stars**: Mostly irrelevant
- ⭐⭐⭐ **3 Stars**: Somewhat relevant
- ⭐⭐⭐⭐ **4 Stars**: Very relevant
- ⭐⭐⭐⭐⭐ **5 Stars**: Critical relevance

### 3. False Positive Flag

Mark an event as a false positive if it:
- Shouldn't have been ingested at all
- Is spam or duplicate content
- Is from an unreliable source
- Contains misleading or false information

### 4. Category Correction

Suggest the correct category if the event was miscategorized:
- Choose from 12 available categories
- Helps train the categorization model
- Improves future automatic classification

### 5. Free-Text Feedback

Provide detailed explanations:
- Why an event is inaccurate
- Additional context not captured
- Suggestions for improvement
- Specific issues with enrichment

## Database Schema

```sql
CREATE TABLE event_feedback (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Ratings (1-5 scale)
    accuracy_rating INTEGER CHECK (accuracy_rating BETWEEN 1 AND 5),
    relevance_rating INTEGER CHECK (relevance_rating BETWEEN 1 AND 5),

    -- Flags
    is_false_positive BOOLEAN DEFAULT FALSE,
    suggested_category VARCHAR(50),  -- If miscategorized

    -- Additional context
    feedback_text TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Submit Feedback

```http
POST /feedback/events/{event_id}
```

**Request Body:**
```json
{
  "accuracy_rating": 4,
  "relevance_rating": 5,
  "is_false_positive": false,
  "suggested_category": null,
  "feedback_text": "Good event, very relevant to our region. Location accuracy could be improved."
}
```

**Response:**
```json
{
  "id": "feedback-uuid",
  "event_id": "event-uuid",
  "user_id": "user-uuid",
  "organization_id": "org-uuid",
  "accuracy_rating": 4,
  "relevance_rating": 5,
  "is_false_positive": false,
  "suggested_category": null,
  "feedback_text": "Good event, very relevant to our region...",
  "created_at": "2025-11-26T14:30:00Z"
}
```

### Get Event Feedback

```http
GET /feedback/events/{event_id}
```

**Response:**
```json
[
  {
    "id": "feedback-uuid",
    "user_email": "analyst@example.org",
    "accuracy_rating": 4,
    "relevance_rating": 5,
    "is_false_positive": false,
    "created_at": "2025-11-26T14:30:00Z"
  }
]
```

### List Feedback with Filters

```http
GET /feedback
```

**Query Parameters:**
- `event_id` (optional) - Filter by specific event
- `user_id` (optional) - Filter by specific user
- `min_accuracy_rating` (optional) - Minimum accuracy rating
- `min_relevance_rating` (optional) - Minimum relevance rating
- `is_false_positive` (optional) - Filter false positives only
- `page` (default: 1) - Page number
- `page_size` (default: 50) - Items per page

### Delete Feedback

```http
DELETE /feedback/{feedback_id}
```

Users can delete their own feedback. Admins can delete any feedback.

## Frontend Integration

### Providing Feedback

Feedback is accessible directly from event cards:

1. **In Stream View**: Click the "Feedback" button on any event card
2. **Quick Options**: Choose from predefined feedback types:
   - ✓ Relevant
   - ⭐ Important
   - ✗ Irrelevant
   - ⚠ Wrong Category
3. **Detailed Feedback**: Click "More Options" for full feedback form

### EventFeedback Component

```tsx
import EventFeedback from './components/EventFeedback';

// In your event display component
<EventFeedback
  eventId={event.event_id}
  onFeedbackSubmitted={() => {
    // Optional: Refresh event or show confirmation
  }}
/>
```

### Feedback UI States

- **Idle**: Feedback button visible
- **Open**: Dropdown menu with quick options
- **Submitted**: Green checkmark confirmation
- **Error**: Red error message (retry available)

## How Feedback Improves the System

### 1. LLM Enrichment Refinement

**Low Accuracy Ratings** trigger:
- Review of enrichment prompts
- Adjustment of extraction rules
- Retraining of categorization models
- Updates to entity recognition

**Example:**
- Multiple users rate events with wrong locations as 1-2 stars
- System reviews location extraction logic
- Improves geocoding accuracy for future events

### 2. Relevance Score Calibration

**Relevance Ratings** inform:
- Relevance score algorithm adjustments
- Category-specific relevance weights
- Regional relevance prioritization
- Source credibility scoring

**Example:**
- Users consistently rate "weather" events as low relevance
- System lowers relevance score for weather category
- Future weather events ranked lower in priority

### 3. False Positive Filtering

**False Positive Flags** enable:
- Source blocklisting for unreliable outlets
- Content pattern detection (spam signatures)
- Duplicate detection improvements
- Noise filtering rules

**Example:**
- Event marked as false positive
- Source URL analyzed for reliability
- Similar events from same source automatically filtered

### 4. Category Correction

**Suggested Categories** improve:
- Automatic categorization accuracy
- Keyword-category mappings
- Context-based classification
- Multi-label categorization

**Example:**
- Event auto-categorized as "political" but users suggest "religious_freedom"
- System learns keywords associated with religious freedom
- Future similar events categorized correctly

## Feedback Analytics

### For Administrators

View aggregate feedback metrics in the Dashboard:

- **Average Accuracy Rating**: Overall enrichment quality
- **Average Relevance Rating**: Content relevance to mission
- **False Positive Rate**: Percentage of flagged events
- **Category Corrections**: Most frequent miscategorizations

### For Developers

Access feedback data programmatically:

```python
from backend.models.feedback import EventFeedback

# Get average ratings for event
avg_accuracy = db.query(func.avg(EventFeedback.accuracy_rating))\
    .filter(EventFeedback.event_id == event_id)\
    .scalar()

# Find events with low relevance
low_relevance_events = db.query(Event)\
    .join(EventFeedback)\
    .filter(EventFeedback.relevance_rating <= 2)\
    .all()

# Identify false positive patterns
false_positives = db.query(Event, func.count(EventFeedback.id))\
    .join(EventFeedback)\
    .filter(EventFeedback.is_false_positive == True)\
    .group_by(Event.source_url)\
    .having(func.count(EventFeedback.id) > 5)\
    .all()
```

## Best Practices

### For Analysts

1. **Provide Feedback Regularly**: Help improve the system for everyone
2. **Be Specific**: Use free-text field to explain issues
3. **Focus on Quality**: Accuracy feedback helps most
4. **Flag False Positives**: Keep the feed clean
5. **Suggest Categories**: Improve categorization accuracy

### For Administrators

1. **Review Feedback Weekly**: Monitor system performance
2. **Act on Patterns**: Address recurring issues promptly
3. **Communicate Improvements**: Let users know feedback led to changes
4. **Encourage Participation**: Remind users to provide feedback

### For Developers

1. **Automate Analysis**: Build dashboards for feedback trends
2. **Prioritize High-Impact**: Focus on issues affecting many users
3. **Close the Loop**: Document improvements made from feedback
4. **Monitor Metrics**: Track accuracy/relevance over time

## Privacy & Ethics

### User Privacy

- Feedback is associated with user account (for accountability)
- User email visible to admins (organization-scoped)
- Free-text feedback should not contain sensitive personal data

### Feedback Usage

- Used **only** for system improvement
- Never shared with external parties
- Aggregated for analytics (de-identified)
- Can be deleted by user or admin

### False Positive Handling

- **No automatic deletion**: Events marked false positive are reviewed manually
- **Human verification**: Admins review false positive flags
- **Source evaluation**: Unreliable sources may be blocklisted
- **Transparency**: Users notified when action taken on feedback

## Troubleshooting

### Feedback Not Submitting

1. **Check permissions**: Ensure you're logged in
2. **Verify event exists**: Event may have been deleted
3. **Check network**: Connection issues may prevent submission

### Can't See Others' Feedback

- Feedback is **organization-scoped** (same org only)
- Only **Admins** can view all feedback
- Regular users see aggregated counts only

### Feedback Not Improving System

- **Time lag**: Changes require retraining (weekly/monthly cycles)
- **Volume needed**: Patterns require multiple feedback instances
- **Manual review**: Some changes require human decision

## Related Documentation

- [Data Model & Multi-Tenancy](DATA_MODEL.md) - Organization-scoped data
- [Audit Logging](AUDIT_LOGGING.md) - Feedback submission is audited
- [Risk Mitigation](RISK_MITIGATION.md) - Ethical use of feedback data

## Future Enhancements

Planned improvements to the feedback system:

- **Bulk Feedback**: Rate multiple events at once
- **Feedback Templates**: Quick feedback for common issues
- **ML Integration**: Automatic pattern detection from feedback
- **Feedback Dashboard**: Dedicated analytics page for admins
- **Notification System**: Alert users when their feedback led to changes

---

**Version**: 0.8.0
**Last Updated**: 2025-11-26
