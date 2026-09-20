import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.product import Product, ProductVersion
from app.models.issue import Issue
from app.models.timeline import IssueUpdate
from app.models.subscription import Subscription
from app.auth.security import hash_password, generate_secure_token
from app.config import settings


def seed_database(db: Session = None):
    close_db = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_db = True

    try:
        # 1. Admin user
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.flush()
            print(f"Created default admin: {settings.ADMIN_EMAIL}")

        # 2. Products
        pro = db.query(Product).filter(Product.slug == "homey-pro").first()
        if not pro:
            pro = Product(name="Homey Pro", slug="homey-pro")
            db.add(pro)

        mini = db.query(Product).filter(Product.slug == "homey-pro-mini").first()
        if not mini:
            mini = Product(name="Homey Pro mini", slug="homey-pro-mini")
            db.add(mini)

        bridge = db.query(Product).filter(Product.slug == "homey-bridge").first()
        if not bridge:
            bridge = Product(name="Homey Bridge", slug="homey-bridge")
            db.add(bridge)

        db.flush()

        # 3. Versions
        v13_5 = db.query(ProductVersion).filter(ProductVersion.version_string == "OS 13.5.0").first()
        if not v13_5:
            v13_5 = ProductVersion(product_id=pro.id, version_string="OS 13.5.0")
            db.add(v13_5)

        v13_4 = db.query(ProductVersion).filter(ProductVersion.version_string == "OS 13.4.1").first()
        if not v13_4:
            v13_4 = ProductVersion(product_id=pro.id, version_string="OS 13.4.1")
            db.add(v13_4)

        db.flush()

        # 4. Check if sample issues already exist
        if db.query(Issue).count() == 0:
            now = datetime.datetime.now(datetime.timezone.utc)
            d1 = now - datetime.timedelta(days=20)
            d2 = now - datetime.timedelta(days=10)
            d3 = now - datetime.timedelta(days=2)

            # Issue 1: IKEA Matter
            issue1 = Issue(
                title="IKEA Matter devices cannot be added",
                slug="ikea-matter-devices-cannot-be-added",
                summary="Some IKEA Matter over Thread and Wi-Fi devices cannot be paired with the smart home gateway.",
                description=(
                    "Users report that attempting to commission newer IKEA Matter products results in a timeout "
                    "during the Thread network joining phase. The gateway logs indicate a rendezvous handshake "
                    "interruption during Bluetooth LE setup."
                ),
                status="Investigating",
                severity="High",
                visibility="Public",
                workaround="Commission devices within 2 meters of the gateway before moving them to their permanent location.",
                expected_fix="Enhanced Thread commissioning timing tolerance in next OS release.",
                first_reported_at=d1,
                confirmed_at=d2,
                last_updated_at=d3,
                min_subscribers_threshold=5,
                auto_publish_on_threshold=True,
            )
            issue1.products.extend([pro, mini, bridge])
            issue1.versions.append(v13_5)
            db.add(issue1)
            db.flush()

            # Timeline for Issue 1
            db.add(IssueUpdate(
                issue_id=issue1.id,
                title="Issue Confirmed by Support",
                description="Our support engineering team has confirmed customer reports and isolated reproducible cases.",
                status_at_update="Investigating",
                update_date=d2,
                notified_subscribers=False
            ))
            db.add(IssueUpdate(
                issue_id=issue1.id,
                title="Investigation Underway",
                description="Engineers have captured Bluetooth LE and Thread sniffer traces and are analyzing the rendezvous packet sequences.",
                status_at_update="Investigating",
                update_date=d3,
                notified_subscribers=False
            ))

            # Sample subscriptions
            for i in range(1, 15):
                db.add(Subscription(
                    issue_id=issue1.id,
                    email=f"user{i}@smart-community.example",
                    status="confirmed" if i <= 12 else "pending",
                    confirmation_token=generate_secure_token(32),
                    unsubscribe_token=generate_secure_token(32),
                    created_at=d2,
                    confirmed_at=d2 if i <= 12 else None
                ))

            # Issue 2: Zigbee availability
            issue2 = Issue(
                title="Some Zigbee devices become unavailable after mesh reorganization",
                slug="some-zigbee-devices-become-unavailable",
                summary="Battery-operated Zigbee sensors intermittently lose connection following routing table updates.",
                description=(
                    "Certain sleep-end devices do not properly receive new parent router addresses when mesh route "
                    "discovery packets are broadcast simultaneously."
                ),
                status="Monitoring",
                severity="Medium",
                visibility="Public",
                workaround="Power-cycle the nearest mains-powered router or manually wake the sensor button once.",
                expected_fix="Optimized parent-child timeout and route discovery retry backoff.",
                fixed_version="OS 13.5.1",
                first_reported_at=now - datetime.timedelta(days=15),
                confirmed_at=now - datetime.timedelta(days=8),
                last_updated_at=now - datetime.timedelta(hours=12),
            )
            issue2.products.extend([pro, bridge])
            issue2.versions.append(v13_4)
            db.add(issue2)
            db.flush()

            db.add(IssueUpdate(
                issue_id=issue2.id,
                title="Candidate Patch Deployed to Beta",
                description="We deployed an updated Zigbee network stack in firmware v13.5.1-rc3. Mesh stability is currently being monitored.",
                status_at_update="Monitoring",
                update_date=now - datetime.timedelta(hours=12),
                notified_subscribers=False
            ))

            # Issue 3: Resolved Temperature widget
            issue3 = Issue(
                title="Temperature values are incorrect in climate dashboard widget",
                slug="temperature-values-incorrect-in-climate-widget",
                summary="Climate overview card displayed corrupted decimal rounding for Celsius values in certain locales.",
                description=(
                    "A locale parsing error caused floating point values with comma separators to truncate decimal digits, "
                    "showing 21.0°C as 2°C in the summary widget."
                ),
                status="Resolved",
                severity="Low",
                visibility="Resolved",
                workaround="Open the individual sensor device tile to see exact decimal telemetry.",
                expected_fix="Locale decimal formatting fix in mobile app.",
                fixed_version="App v8.1.0",
                first_reported_at=now - datetime.timedelta(days=30),
                confirmed_at=now - datetime.timedelta(days=25),
                last_updated_at=now - datetime.timedelta(days=5),
                resolved_at=now - datetime.timedelta(days=5),
            )
            issue3.products.append(pro)
            db.add(issue3)
            db.flush()

            db.add(IssueUpdate(
                issue_id=issue3.id,
                title="Fix Released in App v8.1.0",
                description="The bug has been fixed in the latest mobile app update v8.1.0 now available on Google Play and Apple App Store.",
                status_at_update="Resolved",
                update_date=now - datetime.timedelta(days=5),
                notified_subscribers=False
            ))

            print("Database seeded with sample issues and subscriptions.")

        db.commit()
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed_database()
