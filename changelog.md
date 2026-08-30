# Changelog

> Historical note: versions before v2.0.0 describe the legacy local-database architecture of the project. The current application uses the online PieceHunt API and a different runtime structure.

## [1.0.0] - 2026-05-03
### Added
- WxPython user interface
- User registration and login
- Password hashing
- Email confirmation on registration
- Password reset via code
- GDPR consent checkbox with timestamp
- Adding sets and getting parts
- Database updates
- Stickered image detection + viewer with report button for false positives
- Progress tracking per user
---
---

## [1.1.0] - 2026-05-04
### Changes
- Changed confusing UserHandler and RegisterHandler attributes check_password and password_check    
password_check = only checks if password is entered correctly    
check_password_requirement = only checks minimum requirements

### Added
- Button on main welcome screen to delete an account
---
---

## [1.2.0] - 2026-05-12
### Changes
- .env file : credentials now saved as Base64   
- moved pure script files to a separate folder

### Added
- Logging for the whole application, details in design.md
- Docstrings throughout the whole application
---
---

## [1.2.1] - 2026-05-12
### Changes
- In debug mode when selecting a set the id showed instead of the set number

### Other
- Upgraded to Python 3.14
---
---

## [1.3.0] - 2026-05-17
### Added
- New menu option that opens a window to generate missing pieces report 
- Missing Pieces on pdf
- Missing pieces on excel
- Reports send by email

### Changed
- Enabled Enter button at login and register    
- Changed back to homescreen to Logout      
- Refactored delete text to fit in screen
---
---

## [1.3.1] - 2026-06-13
### Added
- Future design diagrams
- Unit Testing

### Changed
- Removed Keygen from menu, added to a secret key combo

## [1.3.2] - 2026-06-22
### Changed
- excluded demo videos from git
- Removed hard coded version from settings, source of truth pyproject.toml or metadata
- While trying to delete account, now displaying the same message for wrong username or password
- resolved issue where Updater in menubar.py wasn't really using a seperate thread
- set current_user to None when logging out, current_set to None when returning to SetsPanel or logging out
- Show buzy cursor in between adding a set and redrawing sets

### Added
- Added last login date while deleting account

## [2.0.0] - 2026-08-30
### Changed
- Switched from the legacy local-database architecture to an online PieceHunt API-based model
- Reworked authentication around API-backed login/register flows instead of local database user handling
- Centralized API communication in `services/api_client.py` and added automatic token refresh/retry logic in `services/api_retry.py`
- Moved user/session state handling into `UserHandler` and `AuthSession`, with token refresh support for expired sessions
- Kept the desktop wxPython UX, but shifted data access, set loading, and progress tracking to remote API calls
- Kept local image and instruction caching under `data/` so the app still works smoothly offline after content has been downloaded
- Refactored set/part logic to fetch progress and metadata from the API while still managing local files and thumbnails
- Simplified and cleaned the app structure by splitting responsibilities into `services/`, `backend/handlers/`, and `frontend/wx/`
- Removed older local-database assumptions and legacy code paths that were tied to the first project version

### Removed
- Local database dependency from the main runtime flow
- Legacy local user/session logic tied directly to a database model
- Old monolithic data-access patterns that were used in the first version of the project

### Added
- API-first user lifecycle: login, registration, email verification, password reset, account deletion
- Session-aware access-token management with refresh on expired JWTs
- Better separation between UI code, backend logic, and remote API integration
- Structured feedback/reporting endpoints for missing images, false positives, and app issues